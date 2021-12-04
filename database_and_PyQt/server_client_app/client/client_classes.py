import datetime
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
from client.client_functions import user_list_request, contacts_list_request, add_contact, remove_contact

LOG = logging.getLogger('client')


class Client(threading.Thread, QObject):

    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, client_name, database, server_address, server_port):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.client_name = client_name
        self.database = database
        self.server_address = server_address
        self.server_port = server_port
        self.transport = self.prepare_transport()
        self.connection = self.send_presence()
        self.database_locker = threading.Lock()
        self.transport_locker = threading.Lock()
        if self.connection:
            self.user_list_update()
            self.contact_list_update()

    def prepare_transport(self):
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((self.server_address, self.server_port))
        except ConnectionRefusedError:
            LOG.critical(f'Не удалось подключиться к серверу {self.server_address}:{self.server_port}')
            sys.exit(1)
        return transport

    def send_presence(self):
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
        server_message = get_message(self.transport)
        if vrs.RESPONSE in server_message:
            if server_message[vrs.RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {server_message[vrs.ERROR]}'
        raise custom_exceptions.NoResponseInServerMessage

    def create_message(self, action, message=None, destination=None):
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
        message_to_send = self.create_message(vrs.MESSAGE, message, to_client)
        with self.database_locker:
            if not self.database.check_user(to_client):
                LOG.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_client}')
                return
            self.database.save_message('out', to_client, message)
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
        if message.get(vrs.ACTION) == vrs.MESSAGE and \
                vrs.SENDER in message and vrs.MESSAGE_TEXT in message and \
                message.get(vrs.DESTINATION) == self.client_name:
            LOG.debug(f'{self.client_name}: Получено сообщение от {message[vrs.SENDER]}')
            with self.database_locker:
                try:
                    self.database.save_message(
                        'in', message[vrs.SENDER], message[vrs.MESSAGE_TEXT])
                    self.new_message.emit(message[vrs.SENDER])
                except Exception:
                    LOG.error('Ошибка взаимодействия с базой данных')
        else:
            LOG.debug(f'{self.client_name}: Получено сообщение от сервера о некорректном запросе')

    def user_list_update(self):
        try:
            with self.transport_locker:
                users_list = user_list_request(self.transport, self.client_name)
        except custom_exceptions.NoResponseInServerMessage:
            LOG.error('Ошибка запроса списка известных пользователей.')
        else:
            with self.database_locker:
                self.database.add_users(users_list)

    def contact_list_update(self):
        try:
            with self.transport_locker:
                contacts_list = contacts_list_request(self.transport, self.client_name)
        except custom_exceptions.NoResponseInServerMessage:
            LOG.error('Ошибка запроса списка контактов.')
        else:
            with self.database_locker:
                for contact in contacts_list:
                    self.database.add_contact(contact)

    def add_contact(self, contact):
        try:
            with self.transport_locker:
                add_contact(self.transport, self.client_name, contact)
                LOG.debug(f'{self.client_name}: Успешно добавлен контакт {contact}')
        except custom_exceptions.NoResponseInServerMessage:
            LOG.debug(f'{self.client_name}: Не удалось добавить контакт {contact}')

    def remove_contact(self, contact):
        try:
            with self.transport_locker:
                remove_contact(self.transport, self.client_name, contact)
                LOG.debug(f'{self.client_name}: Успешно удалён контакт {contact}')
        except custom_exceptions.NoResponseInServerMessage:
            LOG.debug(f'{self.client_name}: Не удалось удалить контакт {contact}')

    def client_shutdown(self):
        self.connection = False
        with self.transport_locker:
            try:
                send_message(self.transport, self.create_message(vrs.EXIT))
            except OSError:
                pass
        LOG.debug('Клиент завершает работу.')
        time.sleep(0.5)

    def run(self):
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
