# libraries imports
import binascii
import hmac
import logging
import os
import select
import threading
from collections import deque
from socket import socket, AF_INET, SOCK_STREAM

# project modules imports
import common.variables as vrs
import logs.server_log_config
from common.utils import get_message, send_message
from common.descriptors import Port, IpAddress
from common.metaclasses import ServerVerifier
from server.server_storage_class import ServerStorage


LOG = logging.getLogger('server')


class NewConnection:
    """
    Класс-регулитор, объект которого хранит блокировщик потока и переменную-флаг
    """

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
        '200': {vrs.RESPONSE: 200},
        '202': {vrs.RESPONSE: 202, vrs.LIST_INFO: None},
        '205': {vrs.RESPONSE: 205},
        '400': {vrs.RESPONSE: 400, vrs.ERROR: 'Bad Request'},
        '511': {vrs.RESPONSE: 511, vrs.DATA: None},
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
        self.new_connection - объект класса-регулятора
        self.database - объект базы данных
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
            self.autorize_user(message, client)
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
            send_message(client, self.RESPONSES['200'])
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.REMOVE_CONTACT and vrs.ACCOUNT_NAME in message and \
                vrs.USER in message and self.clients_names[message[vrs.USER]] == client:
            self.database.remove_contact(message[vrs.USER], message[vrs.ACCOUNT_NAME])
            send_message(client, self.RESPONSES['200'])
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.USERS_REQUEST and vrs.ACCOUNT_NAME in message and \
                self.clients_names[message[vrs.ACCOUNT_NAME]] == client:
            response = self.RESPONSES['202']
            response[vrs.LIST_INFO] = [user[0] for user in self.database.users_all()]
            send_message(client, response)
            return

        if vrs.ACTION in message and message[vrs.ACTION] == vrs.PUBLIC_KEY_REQUEST and vrs.ACCOUNT_NAME in message:
            response = self.RESPONSES['511']
            response[vrs.DATA] = self.database.get_pubkey(message[vrs.ACCOUNT_NAME])
            if response[vrs.DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = self.RESPONSES['400']
                response[vrs.ERROR] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            return

        response = self.RESPONSES['400']
        response[vrs.ERROR] = 'Запрос некорректен.'
        try:
            send_message(client, response)
        except OSError:
            self.remove_client(client)

    def autorize_user(self, message, client):
        """Метод реализующий авторизцию пользователей"""
        LOG.debug(f'Начата авторизация для {message[vrs.USER]}')
        if message[vrs.USER][vrs.ACCOUNT_NAME] in self.clients_names:
            response = self.RESPONSES['400']
            response[vrs.ERROR] = 'Имя пользователя уже занято.'
            try:
                LOG.debug(f'Имя пользователя уже занято: {response}')
                send_message(client, response)
            except OSError:
                LOG.debug('OS Error')
                pass
            self.clients_list.remove(client)
            client.close()
        elif not self.database.check_user(message[vrs.USER][vrs.ACCOUNT_NAME]):
            response = self.RESPONSES['400']
            response[vrs.ERROR] = 'Пользователь не зарегистрирован.'
            try:
                LOG.debug(f'Пользователь не зарегистрирован: {response}')
                send_message(client, response)
            except OSError:
                pass
            self.clients_list.remove(client)
            client.close()
        else:
            LOG.debug('Correct username, starting passwd check.')
            message_auth = self.RESPONSES['511']
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[vrs.DATA] = random_str.decode('ascii')
            hash_string = hmac.new(self.database.get_hash(message[vrs.USER][vrs.ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash_string.digest()
            LOG.debug(f'Auth message = {message_auth}')
            try:
                send_message(client, message_auth)
                ans = get_message(client)
                LOG.debug(f'Auth client message = {ans}')
            except OSError as err:
                LOG.debug('Error in auth, data:', exc_info=err)
                client.close()
                return
            client_digest = binascii.a2b_base64(ans[vrs.DATA])
            if vrs.RESPONSE in ans and ans[vrs.RESPONSE] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.clients_names[message[vrs.USER][vrs.ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                try:
                    send_message(client, self.RESPONSES['200'])
                    LOG.debug(f'Auth client complete')
                    with self.new_connection.locker:
                        self.new_connection.value = True
                except OSError:
                    self.remove_client(message[vrs.USER][vrs.ACCOUNT_NAME])
                self.database.login_user(
                    message[vrs.USER][vrs.ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[vrs.USER][vrs.PUBLIC_KEY])
            else:
                response = self.RESPONSES['400']
                response[vrs.ERROR] = 'Неверный пароль.'
                LOG.debug(f'Auth wrong = {response}')
                try:
                    send_message(client, response)
                except OSError:
                    pass
                self.clients_list.remove(client)
                client.close()

    def received_messages_processing(self):
        """
        Метод получения сообщений от сокетов клиентов
        :return: None
        """
        for client_with_message in self.receive_data_list:
            try:
                self.process_client_message(get_message(client_with_message), client_with_message)
            except Exception:
                self.remove_client(client_with_message)

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

    def remove_client(self, client):
        """
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        """
        LOG.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.clients_names:
            if self.clients_names[name] == client:
                self.database.logout_user(name)
                del self.clients_names[name]
                break
        self.clients_list.remove(client)
        client.close()

    def service_update_lists(self):
        for client in self.clients_names:
            try:
                send_message(self.clients_names[client], self.RESPONSES['205'])
            except OSError:
                self.remove_client(self.clients_names[client])

    def run(self):
        """
        Основной метод сервера
        :return: None
        """

        LOG.info(f'Запущен сервер. Порт подключений: {self.listen_port}, адрес прослушивания: {self.listen_address}')
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
