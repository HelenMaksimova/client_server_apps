"""Утилиты"""

import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
import custom_exceptions


def get_message(socket):
    """
    Утилита приёма и декодирования сообщения
    принимает байты выдаёт словарь, если приняточто-то другое отдаёт ошибку значения
    :param socket: объект сокета
    :return: словарь
    """

    encoded_response = socket.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise custom_exceptions.IncorrectData
    raise ValueError


def send_message(socket, message):
    """
    Утилита кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param socket: объект сокета
    :param message: сообщение в виде словаря
    :return: None
    """

    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    socket.send(encoded_message)


def print_help():
    """
    Функция для вывода справки по командам сервера
    :return: None
    """
    print('Поддерживаемые комманды:')
    print('users - список известных пользователей')
    print('connected - список подключенных пользователей')
    print('loghist - история входов пользователя')
    print('exit - завершение работы сервера.')
    print('help - вывод справки по поддерживаемым командам')


def main_loop(database):
    """
    Основной цикл сервера с запросом команд
    :param database: объект базы данных сервера
    :return: None
    """
    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for user in sorted(database.users_all()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == 'connected':
            for user in sorted(database.users_active()):
                print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, время установки соединения: {user[3]}')
        elif command == 'loghist':
            name = input(
                'Введите имя пользователя для просмотра истории. Для вывода всей истории просто нажмите Enter: ')
            for user in sorted(database.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')