"""
Модуль, содержащий основной бэк-энд класс клиента, отвечающий за передачу,
получение и обработку сообщений между сервером и клиентом
"""


import binascii
import hashlib
import hmac
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

LOG = logging.getLogger('client')


class Client(threading.Thread, QObject):
    """
    Основной бэк-энд класс клиента, отвечающий за передачу,
    получение и обработку сообщений между сервером и клиентом
    """

    new_message = pyqtSignal(dict)
    connection_lost = pyqtSignal()
    message_205 = pyqtSignal()

    def __init__(self, client_name, password, database, server_address, server_port, keys):
        """
        Метод инициализации. Выставляются основные параметры клиента (имя, объект базы данных и т.д.),
        а также создаётся объект сокета (transport) и объекты локеров потока для базы данных и сокета
        """
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.client_name = client_name
        self.password = password
        self.database = database
        self.server_address = server_address
        self.server_port = server_port
        self.keys = keys
        self.transport = self.prepare_transport()
        self.connection = self.send_presence()
        self.database_locker = threading.Lock()
        self.transport_locker = threading.Lock()
        if self.connection:
            self.user_list_update()
            self.contact_list_update()

    def prepare_transport(self):
        """
        Метод подготовки сокета. Возвращает объект сокета.
        """
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            LOG.critical(f'Не удалось подключиться к серверу {self.server_address}:{self.server_port}')
            sys.exit(1)
        return transport

    def send_presence(self):
        """
        Метод, отвечающий за отправку приветственного сообщения на сервер и прохождение аутентификации.
        В случае успешного подключения и аутентификации возвращает True
        """
        passwd_bytes = self.password.encode('utf-8')
        salt = self.client_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        pubkey = self.keys.publickey().export_key().decode('ascii')

        LOG.debug(f'Passwd hash ready: {passwd_hash_string}')

        try:
            message = {
                vrs.ACTION: vrs.PRESENCE,
                vrs.TIME: time.time(),
                vrs.PORT: self.server_port,
                vrs.USER: {vrs.ACCOUNT_NAME: self.client_name, vrs.PUBLIC_KEY: pubkey}
            }
            send_message(self.transport, message)
            answer = self.presence_answer(passwd_hash_string)
            LOG.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f'Установлено соединение с сервером.')
            return True if answer == '200 : OK' else False
        except json.JSONDecodeError:
            LOG.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except custom_exceptions.NoResponseInServerMessage as error:
            LOG.error(f'Ошибка сообщения сервера {self.server_address}: {error}')

    def presence_answer(self, passwd_hash_string):
        """
        Метод, отвечающий за получение и расшифровку ответа сервера при установлении соединения и аутенификации.
        """
        server_message = get_message(self.transport)
        if vrs.RESPONSE in server_message:
            if server_message[vrs.RESPONSE] == 200:
                return '200 : OK'
            elif server_message[vrs.RESPONSE] == 511:
                ans_data = server_message[vrs.DATA]
                hash_string = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                digest = hash_string.digest()
                my_ans = {
                    vrs.RESPONSE: 511,
                    vrs.DATA: binascii.b2a_base64(digest).decode('ascii')
                }
                send_message(self.transport, my_ans)
                result = self.presence_answer(passwd_hash_string)
                return result
            return f'400 : {server_message[vrs.ERROR]}'
        raise custom_exceptions.NoResponseInServerMessage

    def create_message(self, action, message=None, destination=None):
        """
        Метод, формирующий сообщения в виде словаря для отправки на сервер
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
        Метод, отвечающий за отправку на сервер сообщения для другого пользователя
        """
        message_to_send = self.create_message(vrs.MESSAGE, message, to_client)
        with self.database_locker:
            if not self.database.check_user(to_client):
                LOG.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_client}')
                return
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

    def get_message_from_server(self, message):
        """
        Метод, отвечающий за обработку сообщений с сервера после аутентификации
        """
        if message.get(vrs.ACTION) == vrs.MESSAGE and \
                vrs.SENDER in message and vrs.MESSAGE_TEXT in message and \
                message.get(vrs.DESTINATION) == self.client_name:
            LOG.debug(f'{self.client_name}: Получено сообщение от {message[vrs.SENDER]}')
            self.new_message.emit(message)
        elif message.get(vrs.RESPONSE) == 200:
            LOG.debug(f'Получен ответ сервера {message}')
            return
        elif message.get(vrs.RESPONSE) == 205:
            self.user_list_update()
            self.contacts_list_update()
            self.message_205.emit()
        else:
            LOG.debug(f'{self.client_name}: Получено сообщение от сервера о некорректном запросе')

    def user_list_update(self):
        """
        Метод обновления с сервера списка известных пользователей
        """
        LOG.debug(f'Запрос списка известных пользователей {self.client_name}')
        request = {
            vrs.ACTION: vrs.USERS_REQUEST,
            vrs.TIME: time.time(),
            vrs.ACCOUNT_NAME: self.client_name
        }
        with self.transport_locker:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        if vrs.RESPONSE in answer and answer[vrs.RESPONSE] == 202:
            self.database.add_users(answer[vrs.LIST_INFO])
        else:
            LOG.error('Не удалось обновить список известных пользователей.')

    def contact_list_update(self):
        """
        Метод обновления с сервера контактов пользователя
        """
        self.database.contacts_clear()
        LOG.debug(f'Запрос контакт листа для пользователся {self.client_name}')
        request = {
            vrs.ACTION: vrs.GET_CONTACTS,
            vrs.TIME: time.time(),
            vrs.USER: self.client_name
        }
        LOG.debug(f'Сформирован запрос {request}')
        with self.transport_locker:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        LOG.debug(f'Получен ответ {answer}')
        if vrs.RESPONSE in answer and answer[vrs.RESPONSE] == 202:
            for contact in answer[vrs.LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOG.error('Не удалось обновить список контактов.')

    def add_contact(self, contact):
        """
        Метод добавления контакта пользователя на сервер
        """
        LOG.debug(f'Создание контакта {contact}')
        request = {
            vrs.ACTION: vrs.ADD_CONTACT,
            vrs.TIME: time.time(),
            vrs.USER: self.client_name,
            vrs.ACCOUNT_NAME: contact
        }
        with self.transport_locker:
            send_message(self.transport, request)
            self.get_message_from_server(get_message(self.transport))

    def remove_contact(self, contact):
        """
        Метод удаления контакта пользователя с сервера
        """
        LOG.debug(f'Удаление контакта {contact}')
        request = {
            vrs.ACTION: vrs.REMOVE_CONTACT,
            vrs.TIME: time.time(),
            vrs.USER: self.client_name,
            vrs.ACCOUNT_NAME: contact
        }
        with self.transport_locker:
            send_message(self.transport, request)
            self.get_message_from_server(get_message(self.transport))

    def get_user_pubkey(self, user):
        """
        Метод получения публичного ключа пользователя с сервера
        """
        LOG.debug(f'Запрос публичного ключа для {user}')
        request = {
            vrs.ACTION: vrs.PUBLIC_KEY_REQUEST,
            vrs.TIME: time.time(),
            vrs.ACCOUNT_NAME: user
        }
        with self.transport_locker:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        if vrs.RESPONSE in answer and answer[vrs.RESPONSE] == 511:
            return answer[vrs.DATA]
        else:
            LOG.error(f'Не удалось получить ключ собеседника{user}.')

    def client_shutdown(self):
        """
        Метод завершения работы клиента
        """
        self.connection = False
        with self.transport_locker:
            try:
                send_message(self.transport, self.create_message(vrs.EXIT))
            except OSError:
                pass
        LOG.debug('Клиент завершает работу.')
        time.sleep(0.5)

    def run(self):
        """
        Основной метод клиента. Пока параметр соединения (connection) True,
        раз в секунду проверяет сокет на наличие сообщений от сервера и
        при наличии таковых отправляет их на обработку.
        """
        LOG.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.connection:
            time.sleep(1)
            with self.transport_locker:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        LOG.critical(f'Потеряно соединение с сервером.')
                        self.connection = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOG.debug(f'Потеряно соединение с сервером.')
                    self.connection = False
                    self.connection_lost.emit()
                else:
                    LOG.debug(f'Принято сообщение с сервера: {message}')
                    self.get_message_from_server(message)
                finally:
                    self.transport.settimeout(5)
