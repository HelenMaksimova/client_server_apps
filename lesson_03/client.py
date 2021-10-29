"""Программа-клиент"""

import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, PORT
from common.utils import get_message, send_message
import argparse


def create_presence_message(port=DEFAULT_PORT, acc_name='Guest'):
    """
    Функция генерирует запрос о присутствии клиента
    :param acc_name: логин (имя аккауната)
    :param port: порт клиента
    :return: сообщение-запрос о присутствии клиента (словарь)
    """
    result_message = {
        ACTION: PRESENCE,
        TIME: time.time(),
        PORT: port,
        USER: {
            ACCOUNT_NAME: acc_name
        }
    }
    return result_message


def process_answer(server_message):
    """
    Функция разбирает ответ сервера
    :param server_message: ответ сервера
    :return: код ответа сервера (строка)
    """
    if RESPONSE in server_message:
        if server_message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {server_message[ERROR]}'
    raise ValueError


def main():
    """
    Загружаем параметы коммандной строки
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, default=DEFAULT_PORT)
    parser.add_argument('address', nargs='?', type=str, default=DEFAULT_IP_ADDRESS)

    args = parser.parse_args()

    try:
        server_port = args.port
        server_address = args.address
        if not(1024 < server_port < 65535):
            raise ValueError
    except ValueError:
        print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    # Инициализация сокета и обмен

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence_message(server_port)
    send_message(transport, message_to_server)
    try:
        answer = process_answer(get_message(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    main()
