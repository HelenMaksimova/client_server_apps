"""Программа-клиент"""

import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, PORT
from common.utils import get_message, send_message
import argparse
import logs.client_log_config
import logging
import custom_exceptions


LOG = logging.getLogger('client')


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
    raise custom_exceptions.NoResponseInServerMessage


def main():
    """
    Загружаем параметы коммандной строки
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, default=DEFAULT_PORT)
    parser.add_argument('address', nargs='?', type=str, default=DEFAULT_IP_ADDRESS)

    args = parser.parse_args()

    server_port = args.port
    server_address = args.address

    try:
        if not(1024 < server_port < 65535):
            raise custom_exceptions.PortOutOfRange
    except custom_exceptions.PortOutOfRange as error:
        LOG.critical(f'Ошибка порта {server_port}: {error}. Соединение закрывается.')
        sys.exit(1)

    # Инициализация сокета и обмен

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence_message(server_port)
    send_message(transport, message_to_server)
    LOG.info(f'Отправлено сообщение {message_to_server[ACTION]} '
             f'от пользователя {message_to_server[USER][ACCOUNT_NAME]} '
             f'для сервера {server_address}')
    try:
        answer = process_answer(get_message(transport))
        LOG.info(f'Получен ответ от сервера {server_address}: {answer}')
    except json.JSONDecodeError:
        LOG.error(f'Не удалось декодировать сообщение сервера {server_address}.')
    except custom_exceptions.NoResponseInServerMessage as error:
        LOG.error(f'Ошибка сообщения сервера {server_address}: {error}')


if __name__ == '__main__':
    main()
