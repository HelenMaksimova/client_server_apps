# libraries imports
import argparse
import logging
import sys
import select
import time
from collections import deque
from socket import socket, AF_INET, SOCK_STREAM

# project modules imports
import common.variables as vrs
import custom_exceptions
import logs.server_log_config
from decos import Log
from common.utils import get_message, send_message


LOG = logging.getLogger('server')
LOG_F = logging.getLogger('server_func')


class Server:
    """
    Класс сервера
    """

    RESPONSES = {
        'OK': {vrs.RESPONSE: 200},
        'BAD_REQUEST': {vrs.RESPONSE: 400, vrs.ERROR: 'Bad Request'}
    }

    @Log(LOG_F)
    def __init__(self):
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
        self.listen_port, self.listen_address = self.get_params()
        self.transport = self.prepare_socket()
        LOG.debug(f'Создан объект сервера')

    @Log(LOG_F)
    def prepare_socket(self):
        """
        Метод подготовки и запуска сокета сервера
        :return: сокет сервера
        """
        transport = socket(AF_INET, SOCK_STREAM)
        transport.bind((self.listen_address, self.listen_port))
        transport.settimeout(1)
        transport.listen(vrs.MAX_CONNECTIONS)
        LOG.info(f'Запущен сервер. Порт подключений: {self.listen_port}, адрес прослушивания: {self.listen_address}')
        return transport

    @Log(LOG_F)
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
                send_message(client, self.RESPONSES.get('OK'))
                LOG.debug(f'Клиент {client_name} зарегестрирован на сервере')
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
            self.clients_names[message[vrs.ACCOUNT_NAME]].close()
            LOG.debug(f'Клиент {message[vrs.ACCOUNT_NAME]} вышел из чата. Клиент отключён от сервера.')
            del self.clients_names[message[vrs.ACCOUNT_NAME]]
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
                self.clients_list.remove(client_with_message)

    @Log(LOG_F)
    def send_messages_to_clients(self):
        """
        Метод отправки сообщений клиентам
        :return: None
        """
        while self.messages_deque:
            message = self.messages_deque.popleft()
            waiting_client = self.clients_names[message[vrs.DESTINATION]]
            if waiting_client in self.send_data_list:
                try:
                    send_message(waiting_client, message)
                    LOG.info(f'Сообщение клиента {message[vrs.SENDER]} отправлено клиенту {message[vrs.DESTINATION]}')
                except Exception:
                    LOG.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    waiting_client.close()
                    self.clients_list.remove(waiting_client)

    def run(self):
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

    @staticmethod
    @Log(LOG_F)
    def get_params():
        """
        Метод получения параметров при запуске из комадной строки
        :return: кортеж параметров
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', type=int, default=vrs.DEFAULT_PORT)
        parser.add_argument('-a', type=str, default='')
        args = parser.parse_args()
        try:
            if not (1024 < args.p < 65535):
                raise custom_exceptions.PortOutOfRange
        except custom_exceptions.PortOutOfRange as error:
            LOG.critical(f'Ошибка порта {args.p}: {error}. Соединение закрывается.')
            sys.exit(1)
        return args.p, args.a
