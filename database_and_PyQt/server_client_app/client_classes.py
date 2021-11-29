import logging
import time
import json
import threading

import custom_exceptions
import common.variables as vrs
import logs.client_log_config
from common.utils import send_message, get_message
from client_functions import add_contact, remove_contact

LOG = logging.getLogger('client')


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


class ClientSender(threading.Thread):
    """
    Класс клиента
    """

    def __init__(self, client_name, transport, database):
        """
        Метод инициализации
        """
        self.client_name = client_name
        self.transport = transport
        self.database = database
        self.database_locker = threading.Lock()
        self.transport_locker = threading.Lock()
        super().__init__()

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
        Метод взаимодействия клиента с пользователем
        :return: None
        """
        print(self.client_name)
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.send_message_to_server(*self.input_message())
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                with self.transport_locker:
                    try:
                        send_message(self.transport, self.create_message(vrs.EXIT))
                    except Exception:
                        pass
                print('Завершение соединения.')
                LOG.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            elif command == 'contacts':
                with self.database_locker:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == 'edit':
                self.edit_contacts()
            elif command == 'history':
                self.print_history()
            else:
                print('Команда не распознана, попробуйте снова. help - вывести поддерживаемые команды.')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with self.database_locker:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.client_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.client_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: '
                          f'{message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contacts(self):

        answer = input('Для удаления введите del, для добавления add: ')

        if answer == 'del':
            username = input('Введите имя удаляемного контакта: ')
            with self.database_locker:
                if self.database.check_contact(username):
                    self.database.del_contact(username)
                    with self.transport_locker:
                        try:
                            remove_contact(self.transport, self.client_name, username)
                        except custom_exceptions.NoResponseInServerMessage:
                            LOG.error('Не удалось отправить информацию на сервер.')
                else:
                    LOG.error('Попытка удаления несуществующего контакта.')

        elif answer == 'add':
            username = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(username):
                with self.database_locker:
                    self.database.add_contact(username)
                with self.transport_locker:
                    try:
                        add_contact(self.transport, self.client_name, username)
                    except custom_exceptions.NoResponseInServerMessage:
                        LOG.error('Не удалось отправить информацию на сервер.')

    @staticmethod
    def print_help():
        """
        Метод, выводящий справку по использованию
        """
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
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
