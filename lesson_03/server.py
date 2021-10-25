"""Программа-сервер"""

import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message
import argparse


def process_client_message(client_message):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param client_message: сообщение от клиента в виде словаря
    :return: ответ сервера в виде словаря
    """
    if ACTION in client_message and client_message[ACTION] == PRESENCE and TIME in client_message \
            and USER in client_message and client_message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONDEFAULT_IP_ADDRESSSE: 400,
        ERROR: 'Bad Request'
    }


def main():
    """
    Загрузка параметров командной строки, если нет параметров, то задаём значения по умоланию.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=DEFAULT_PORT)
    parser.add_argument('-a', type=str, default='')

    args = parser.parse_args()

    # загружаем порт

    try:
        listen_port = args.p
        if not(1024 < listen_port < 65535):
            raise ValueError
    except ValueError:
        print(
            'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)

    # загружаем какой адрес слушать

    listen_address = args.a

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        try:
            message_from_client = get_message(client)
            print(message_from_client)
            response = process_client_message(message_from_client)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Принято некорретное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()
