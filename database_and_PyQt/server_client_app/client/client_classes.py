import logging
import socket
import sys
import time
import json
import threading
from PyQt5.QtCore import QObject, pyqtSignal

import common.custom_exceptions as custom_exceptions
import common.variables as vrs
import logs.client_log_config
from common.utils import send_message, get_message
from client_functions import user_list_request, contacts_list_request

LOG = logging.getLogger('client')


class Client(threading.Thread, QObject):
    """
    Класс клиента
    """

    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, client_name, database):
        """
        Метод инициализации
        """
        self.client_name = client_name
        self.transport = self.prepare_transport()
        self.database = database
        self.database_locker = threading.Lock()
        self.transport_locker = threading.Lock()
        super().__init__()

    def prepare_transport(self):
        """
        Метод подготовки сокета клиента
        :return: сокет клиента
        """
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            LOG.critical(f'Не удалось подключиться к серверу {self.server_address}:{self.server_port}')
            sys.exit(1)
        return transport

    def fill_database(self):
        try:
            users_list = user_list_request(self.transport, self.client_name)
        except custom_exceptions.NoResponseInServerMessage:
            LOG.error('Ошибка запроса списка известных пользователей.')
        else:
            self.database.add_users(users_list)

        try:
            contacts_list = contacts_list_request(self.transport, self.client_name)
        except custom_exceptions.NoResponseInServerMessage:
            LOG.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                self.database.add_contact(contact)

    def send_presence(self):
        """
        Метод отправки приветственного сообщения на сервер.
        В случае ответа сервера об успешном подключении возвращает True
        :return: True или False
        """
        try:
            message = {
                vrs.ACTION: vrs.PRESENCE,
                vrs.TIME: time.time(),
                vrs.PORT: self.server_port,
                vrs.USER: {vrs.ACCOUNT_NAME: self.client_name}
            }
            send_message(self.transport, message)
            answer = self.presence_answer()
            LOG.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f'Установлено соединение с сервером.')
            return True if answer == '200 : OK' else False
        except json.JSONDecodeError:
            LOG.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except custom_exceptions.NoResponseInServerMessage as error:
            LOG.error(f'Ошибка сообщения сервера {self.server_address}: {error}')

    def presence_answer(self):
        """
        Метод обработки ответа сервера на приветственное сообщение
        :return: ответ сервера в виде строки
        """
        server_message = get_message(self.transport)
        if vrs.RESPONSE in server_message:
            if server_message[vrs.RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {server_message[vrs.ERROR]}'
        raise custom_exceptions.NoResponseInServerMessage

    def create_message(self, action, message=None, destination=None):
        """
        Метод создания сообщений
        :param action: тип действия
        :param message: текст сообщения
        :param destination: адресат сообщения
        :return: сообщение в виде словаря
        """

        _, port = self.transport.getpeername()

        result_message = {
            vrs.ACTION: action,
            vrs.TIME: time.time(),
            vrs.PORT: port,
        }

        if action == vrs.MESSAGE and message and destination:
            result_message[vrs.SENDER] = self.client_name
            result_message[vrs.MESSAGE_TEXT] = message
            result_message[vrs.DESTINATION] = destination

        elif action == vrs.EXIT:
            result_message[vrs.ACCOUNT_NAME] = self.client_name

        return result_message

    def send_message_to_server(self, to_client, message):
        """
        Метод отправки сообщений на сервер для других клиентов
        :param to_client: адресат
        :param message: сообщение
        :return: None
        """
        message_to_send = self.create_message(vrs.MESSAGE, message, to_client)
        with self.database_locker:
            if not self.database.check_user(to_client):
                LOG.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_client}')
                return
            self.database.save_message(self.client_name, to_client, message)
        with self.transport_locker:
            try:
                send_message(self.transport, message_to_send)
                LOG.info(f'{self.client_name}: Отправлено сообщение для пользователя {to_client}')
            except OSError as error:
                if error.errno:
                    LOG.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    LOG.error('Не удалось передать сообщение. Таймаут соединения')

    def run(self):
        """
        Метод обработки сообщений с сервера от других клиентов
        :return: None
        """
        while True:
            time.sleep(1)
            with self.transport_locker:
                try:
                    message = get_message(self.transport)
                    if message.get(vrs.ACTION) == vrs.MESSAGE and \
                            vrs.SENDER in message and vrs.MESSAGE_TEXT in message and \
                            message.get(vrs.DESTINATION) == self.client_name:
                        LOG.debug(f'{self.client_name}: Получено сообщение от {message[vrs.SENDER]}')
                        with self.database_locker:
                            try:
                                self.database.save_message(
                                    message[vrs.SENDER], self.client_name, message[vrs.MESSAGE_TEXT])
                            except Exception:
                                LOG.error('Ошибка взаимодействия с базой данных')
                    else:
                        LOG.debug(f'{self.client_name}: Получено сообщение от сервера о некорректном запросе')
                        print(f'\nПолучено сообщение от сервера о некорректном запросе: {message}')
                except custom_exceptions.IncorrectData as error:
                    LOG.error(f'Ошибка: {error}')
                except (OSError, ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    LOG.critical(f'Потеряно соединение с сервером.')
                    break
