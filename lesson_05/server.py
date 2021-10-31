"""Программа-сервер"""

import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE, PORT
from common.utils import get_message, send_message
import argparse
import custom_exceptions
import logging
import logs.server_log_config

LOG = logging.getLogger('server')


def process_client_message(client_message):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    возвращает словарь-ответ для клиента

    :param client_message: сообщение от клиента в виде словаря
    :return: ответ сервера в виде словаря
    """
    if ACTION in client_message and client_message[ACTION] == PRESENCE and TIME in client_message \
            and USER in client_message and PORT in client_message and client_message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
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
    listen_port = args.p

    try:
        if not(1024 < listen_port < 65535):
            raise custom_exceptions.PortOutOfRange
    except custom_exceptions.PortOutOfRange as error:
        LOG.critical(f'Ошибка порта {listen_port}: {error}. Соединение закрывается.')
        sys.exit(1)

    # загружаем какой адрес слушать

    listen_address = args.a

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    LOG.info(f'Запущен сервер. Порт подключений: {listen_port}, адрес прослушивания: {listen_address}')

    while True:
        client, client_address = transport.accept()
        LOG.info(f'Установлено соединение с клиентом {client_address}')
        try:
            message_from_client = get_message(client)
            LOG.debug(f'Получено сообщение {message_from_client} от клиента {client_address}')
            response = process_client_message(message_from_client)
            send_message(client, response)
            LOG.info(f'Отправлено сообщение {response} клиенту {client_address}')
        except json.JSONDecodeError:
            LOG.error(f'Не удалось декодировать сообщение клиента {client_address}.')
        except custom_exceptions.IncorrectData as error:
            LOG.error(f'Ошибка сообщения от клиента {client_address}: {error}')
        finally:
            LOG.info(f'Соединение с клиентом {client_address} закрывается')
            client.close()


if __name__ == '__main__':
    main()
