import argparse
import json
import logging
import socket
import sys
import time

import custom_exceptions
from client_classes import ClientSender, ClientReceiver
from client_functions import user_list_request, contacts_list_request
from client_storage_class import ClientStorage
from common.utils import get_message, send_message
from descriptors import Port, IpAddress
import common.variables as vrs
from metaclasses import ClientVerifier

LOG = logging.getLogger('client')


class ClientManager(metaclass=ClientVerifier):

    server_port = Port()
    server_address = IpAddress()

    def __init__(self):
        self.server_port, self.server_address, self.client_name = self.get_params()
        self.transport = self.prepare_transport()
        self.database = ClientStorage(self.client_name)

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

    def get_params(self):
        """
        Метод получения параметров при запуске из комадной строки
        :return: кортеж параметров
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('port', nargs='?', type=int, default=vrs.DEFAULT_PORT)
        parser.add_argument('address', nargs='?', type=str, default=vrs.DEFAULT_IP_ADDRESS)
        parser.add_argument('-n', '--name', type=str, default='Guest')

        args = parser.parse_args()

        server_port = args.port
        server_address = args.address
        client_name = args.name if args.name.strip() else self.input_username()

        return server_port, server_address, client_name

    def run(self):
        print('Консольный месседжер. Клиентский модуль.')
        LOG.info(
            f'Запущен клиент с парамертами: '
            f'адрес сервера: {self.server_address} , порт: {self.server_port}, имя пользователя: {self.client_name}')
        if self.send_presence():
            self.fill_database()
            module_sender = ClientSender(self.client_name, self.transport, self.database)
            module_sender.daemon = True
            module_sender.start()
            LOG.debug('Запущены процессы')

            module_receiver = ClientReceiver(self.client_name, self.transport, self.database)
            module_receiver.daemon = True
            module_receiver.start()

            while True:
                time.sleep(1)
                if module_receiver.is_alive() and module_sender.is_alive():
                    continue
                break

    @staticmethod
    def input_username():
        while True:
            username = input('Имя пользователя не задано при запуске. Введите имя пользователя:')
            if username.strip():
                break
        return username
