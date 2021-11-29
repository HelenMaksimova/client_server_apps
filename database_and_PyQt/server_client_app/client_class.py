import argparse
import socket
import sys
import logging
import time
import json
import threading

import custom_exceptions
import common.variables as vrs
import logs.client_log_config
from common.utils import send_message, get_message
from metaclasses import ClientVerifier
from descriptors import Port, IpAddress

LOG = logging.getLogger('client')
LOG_F = logging.getLogger('client_func')


class ClientSender:
    pass


class ClientReceiver(threading.Thread):

    def __init__(self, client_name, transport, database):
        self.client_name = client_name
        self.transport = transport
        self.database = database
        self.transport_locker = threading.Lock()
        self.database_locker = threading.Lock()
        super().__init__()

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
                        print(f'\n<<{message[vrs.SENDER]}>> : {message[vrs.MESSAGE_TEXT]}')
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


class ClientManager:

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

    def send_presence(self):
        """
        Метод отправки приветственного сообщения на сервер.
        В случае ответа сервера об успешном подключении возвращает True
        :return: True или False
        """
        try:
            send_message(self.transport, self.create_message(vrs.PRESENCE))
            answer = self.presence_answer()
            LOG.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f'Установлено соединение с сервером.')
            return True if answer == '200 : OK' else False
        except json.JSONDecodeError:
            LOG.error('Не удалось декодировать полученную Json строку.')
            sys.exit(1)
        except custom_exceptions.NoResponseInServerMessage as error:
            LOG.error(f'Ошибка сообщения сервера {self.server_address}: {error}')


class Client(metaclass=ClientVerifier):
    """
    Класс клиента
    """

    # для проверки работы метакласса
    # a = socket.socket()

    server_port = Port()
    server_address = IpAddress()

    def __init__(self):
        """
        Метод инициализации
        self.server_port - порт сервера
        self.server_address - адрес сервера
        self.client_name - имя клиента
        self.transport - сокет клиента
        """
        self.server_port, self.server_address, self.client_name = self.get_params()
        self.transport = self.prepare_transport()

    def create_message(self, action, message=None, destination=None):
        """
        Метод создания сообщений
        :param action: тип действия
        :param message: текст сообщения
        :param destination: адресат сообщения
        :return: сообщение в виде словаря
        """
        result_message = {
            vrs.ACTION: action,
            vrs.TIME: time.time(),
            vrs.PORT: self.server_port,
        }

        if action == vrs.PRESENCE:
            result_message[vrs.USER] = {vrs.ACCOUNT_NAME: self.client_name}

        elif action == vrs.MESSAGE and message and destination:
            result_message[vrs.SENDER] = self.client_name
            result_message[vrs.MESSAGE_TEXT] = message
            result_message[vrs.DESTINATION] = destination

        elif action == vrs.EXIT:
            result_message[vrs.ACCOUNT_NAME] = self.client_name

        return result_message

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

    def send_message_to_server(self, to_client, message):
        """
        Метод отправки сообщений на сервер для других клиентов
        :param to_client: адресат
        :param message: сообщение
        :return: None
        """
        message_to_send = self.create_message(vrs.MESSAGE, message, to_client)
        try:
            send_message(self.transport, message_to_send)
            LOG.info(f'{self.client_name}: Отправлено сообщение для пользователя {to_client}')
        except Exception:
            LOG.critical('Потеряно соединение с сервером.')
            sys.exit(1)


    def user_interactive(self):
        """
        Метод взаимодействия клиента с пользователем
        :return: None
        """
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.send_message_to_server(*self.input_message())
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(self.transport, self.create_message(vrs.EXIT))
                print('Завершение соединения.')
                LOG.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')


    def run(self):
        """
        Основной метод клиента
        :return: None
        """
        print(self.client_name)
        if self.send_presence():
            receiver = threading.Thread(target=self.process_server_message)
            receiver.daemon = True
            receiver.start()

            user_interface = threading.Thread(target=self.user_interactive)
            user_interface.daemon = True
            user_interface.start()
            LOG.debug(f'{self.client_name}: Запущены процессы')

            while True:
                time.sleep(1)
                if receiver.is_alive() and user_interface.is_alive():
                    continue
                break

    @staticmethod
    def print_help():
        """
        Метод, выводящий справку по использованию
        """
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    @staticmethod
    def input_message():
        """
        Метод для получения адресата и сообщения от пользователя
        :return: кортеж строк
        """
        while True:
            to_client = input('Введите имя пользователя-адресата:')
            message = input('Введите сообщение:')
            if to_client.strip() and message.strip():
                break
            else:
                print('Имя пользователя и сообщение не может быть пустым!')
        return to_client, message

    @staticmethod
    def get_params():
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
        client_name = args.name

        try:
            if not (1024 < server_port < 65535):
                raise custom_exceptions.PortOutOfRange
        except custom_exceptions.PortOutOfRange as error:
            LOG.critical(f'Ошибка порта {server_port}: {error}. Соединение закрывается.')
            sys.exit(1)
        return server_port, server_address, client_name
