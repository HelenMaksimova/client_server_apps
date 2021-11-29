# libraries imports
import argparse
import logging
import sys
import select
import threading
import time
from collections import deque
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM

# project modules imports
import common.variables as vrs
import logs.server_log_config
from common.utils import get_message, send_message
from descriptors import Port, IpAddress
from metaclasses import ServerVerifier
from server_storage_class import ServerStorage


LOG = logging.getLogger('server')


class NewConnection:

    def __init__(self):
        self.value = False
        self.locker = threading.Lock()

    def set_true(self):
        self.value = True

    def set_false(self):
        self.value = False


class Server(threading.Thread, metaclass=ServerVerifier):
    """
    Класс сервера
    """

    RESPONSES = {
        'OK': {vrs.RESPONSE: 200},
        'BAD_REQUEST': {vrs.RESPONSE: 400, vrs.ERROR: 'Bad Request'},
        '202': {vrs.RESPONSE: 202, vrs.LIST_INFO: None},
    }

    listen_port = Port()
    listen_address = IpAddress()

    def __init__(self, listen_port, listen_address, db_path, new_connection):
        """
        Метод инициализации
        self.clients_names - словарь зарегистрированых пользователей
        self.clients_list - список подключённых пользователей
        self.messages_deque - очередь сообщений пользователей
        self.receive_data_list - список сокетов на получение
        self.send_data_list - список сокетов на отправку
        self.errors_list - список сокетов с ошибками
        self.listen_port - прослушиваемый порт
        self.listen_address - прослушиваемый адрес
        self.transport - сокет сервера
        """
        self.clients_names = dict()
        self.clients_list = []
        self.messages_deque = deque()
        self.receive_data_list = []
        self.send_data_list = []
        self.errors_list = []
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.transport = self.prepare_socket()
        self.new_connection = new_connection
        self.database = ServerStorage(db_path)
        super().__init__()
        LOG.debug(f'Создан объект сервера')

    def prepare_socket(self):
        """
        Метод подготовки и запуска сокета сервера
        :return: сокет сервера
        """
        transport = socket(AF_INET, SOCK_STREAM)
        # для проверки работы метакласса
        # transport = socket(AF_INET, SOCK_DGRAM)
        # transport.connect('127.0.0.1')
        transport.bind((self.listen_address, self.listen_port))
        transport.settimeout(1)
        transport.listen(vrs.MAX_CONNECTIONS)
        return transport

    def process_client_message(self, message, client):
        """
        Метод обработки сообщений клиентов
        :param message: сообщение клиента
        :param client: сокет клиента
        :return: None
        """
        if message.get(vrs.ACTION) == vrs.PRESENCE and vrs.USER in message and \
                vrs.TIME in message and vrs.PORT in message:
            client_name = message[vrs.USER][vrs.ACCOUNT_NAME]
            if client_name not in self.clients_names:
                self.clients_names[client_name] = client
                client_ip, client_port = client.getpeername()
                self.database.login_user(client_name, client_ip, client_port)
                send_message(client, self.RESPONSES.get('OK'))
                LOG.debug(f'Клиент {client_name} зарегестрирован на сервере')
                with self.new_connection.locker:
                    self.new_connection.value = True
            else:
                response = self.RESPONSES['BAD_REQUEST']
                response[vrs.ERROR] = f'Имя пользователя {client_name} уже занято.'
                send_message(client, response)
                self.clients_list.remove(client)
                client.close()
                LOG.error(f'Имя пользователя {client_name} уже занято. Клиент отключён.')
            return

        if message.get(vrs.ACTION) == vrs.MESSAGE and vrs.MESSAGE_TEXT in message and \
                vrs.SENDER in message and vrs.DESTINATION in message and \
                message.get(vrs.DESTINATION) in self.clients_names:
            self.messages_deque.append(message)
            LOG.debug(f'Сообщение клиента {message[vrs.SENDER]} '
                      f'для клиента {message[vrs.DESTINATION]} добавлено в очередь сообщений')
            return

        if message.get(vrs.ACTION) == vrs.EXIT and vrs.ACCOUNT_NAME in message:
            self.clients_list.remove(self.clients_names[message[vrs.ACCOUNT_NAME]])
            self.database.logout_user(message[vrs.ACCOUNT_NAME])
            self.clients_names[message[vrs.ACCOUNT_NAME]].close()
            LOG.debug(f'Клиент {message[vrs.ACCOUNT_NAME]} вышел из чата. Клиент отключён от сервера.')
            del self.clients_names[message[vrs.ACCOUNT_NAME]]
            with self.new_connection.locker:
                self.new_connection.value = True
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.GET_CONTACTS and vrs.USER in message and \
                self.clients_names[message[vrs.USER]] == client:
            response = self.RESPONSES['202']
            response[vrs.LIST_INFO] = self.database.get_contacts(message[vrs.USER])
            send_message(client, response)
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.ADD_CONTACT and vrs.ACCOUNT_NAME in message and \
                vrs.USER in message and self.clients_names[message[vrs.USER]] == client:
            self.database.add_contact(message[vrs.USER], message[vrs.ACCOUNT_NAME])
            send_message(client, self.RESPONSES['OK'])
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.REMOVE_CONTACT and vrs.ACCOUNT_NAME in message and \
                vrs.USER in message and self.clients_names[message[vrs.USER]] == client:
            self.database.remove_contact(message[vrs.USER], message[vrs.ACCOUNT_NAME])
            send_message(client, self.RESPONSES['OK'])
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.USERS_REQUEST and vrs.ACCOUNT_NAME in message and \
                self.clients_names[message[vrs.ACCOUNT_NAME]] == client:
            response = self.RESPONSES['202']
            response[vrs.LIST_INFO] = [user[0] for user in self.database.users_all()]
            send_message(client, response)
            return

        send_message(client, self.RESPONSES.get('BAD_REQUEST'))
        return

    def received_messages_processing(self):
        """
        Метод получения сообщений от сокетов клиентов
        :return: None
        """
        for client_with_message in self.receive_data_list:
            try:
                self.process_client_message(get_message(client_with_message), client_with_message)
            except Exception:
                LOG.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                for name in self.clients_names:
                    if self.clients_names[name] == client_with_message:
                        self.database.logout_user(name)
                        del self.clients_names[name]
                        break
                self.clients_list.remove(client_with_message)

    def send_messages_to_clients(self):
        """
        Метод отправки сообщений клиентам
        :return: None
        """
        while self.messages_deque:
            message = self.messages_deque.popleft()
            waiting_client = self.clients_names[message[vrs.DESTINATION]]
            if waiting_client in self.send_data_list and message[vrs.DESTINATION] in self.clients_names:
                try:
                    send_message(waiting_client, message)
                    self.database.process_message(message[vrs.SENDER], message[vrs.DESTINATION])
                    LOG.info(f'Сообщение клиента {message[vrs.SENDER]} отправлено клиенту {message[vrs.DESTINATION]}')
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    LOG.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    waiting_client.close()
                    self.clients_list.remove(waiting_client)
                    self.database.logout_user(message[vrs.DESTINATION])
                    del self.clients_names[message[vrs.DESTINATION]]
            else:
                LOG.error(f'Пользователь {message[vrs.DESTINATION]} не зарегистрирован на сервере, '
                          f'отправка сообщения невозможна.')

    def run(self):
        LOG.info(f'Запущен сервер. Порт подключений: {self.listen_port}, адрес прослушивания: {self.listen_address}')
        """
        Основной метод сервера
        :return: None
        """
        while True:
            try:
                client, client_address = self.transport.accept()
            except OSError:
                pass
            else:
                LOG.info(f'Установлено соедение с клиентом {client_address}')
                self.clients_list.append(client)

            self.receive_data_list = []
            self.send_data_list = []
            self.errors_list = []
            try:
                if self.clients_list:
                    self.receive_data_list, self.send_data_list, self.errors_list = \
                        select.select(self.clients_list, self.clients_list, [], 0)
            except OSError:
                pass

            self.received_messages_processing()

            if self.messages_deque and self.send_data_list:
                self.send_messages_to_clients()
