"""Программа-сервер"""

import socket
import sys
import json
import time
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, PORT, SENDER
from common.utils import get_message, send_message
import argparse
import custom_exceptions
import logging
import logs.server_log_config
from decos import Log
import select
from collections import deque

LOG = logging.getLogger('server')


@Log(LOG)
def process_client_message(message, messages_list, client):
    """
    Обработчик сообщений от клиентов, принимает словарь -
    сообщение от клинта, проверяет корректность,
    отправляет ответ клиенту или добавляет сообщение в список сообщений для отправки
    :param message: сообщение от клиента в виде словаря
    :param messages_list: список сообщений для отправки
    :param client: сокет клиента
    """
    if ACTION in message and TIME in message and USER in message and PORT in message:
        if message[ACTION] == PRESENCE and message[USER][ACCOUNT_NAME] == 'Guest':
            send_message(client, {RESPONSE: 200})
            return
        if message[ACTION] == MESSAGE and MESSAGE_TEXT in message:
            messages_list.append((message[USER][ACCOUNT_NAME], message[MESSAGE_TEXT]))
            return
    send_message(client,
                 {
                     RESPONSE: 400,
                     ERROR: 'Bad Request'
                 })
    return


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=DEFAULT_PORT)
    parser.add_argument('-a', type=str, default='')

    args = parser.parse_args()

    # загружаем порт
    listen_port = args.p

    try:
        if not (1024 < listen_port < 65535):
            raise custom_exceptions.PortOutOfRange
    except custom_exceptions.PortOutOfRange as error:
        LOG.critical(f'Ошибка порта {listen_port}: {error}. Соединение закрывается.')
        sys.exit(1)

    # загружаем какой адрес слушать

    listen_address = args.a

    # список клиентов и очередь сообщений:
    clients_list = []
    messages_deque = deque()

    # Готовим сокет

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)

    # Слушаем порт

    transport.listen(MAX_CONNECTIONS)

    LOG.info(f'Запущен сервер. Порт подключений: {listen_port}, адрес прослушивания: {listen_address}')

    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            LOG.info(f'Установлено соедение с клиентом {client_address}')
            clients_list.append(client)

        receive_data_list = []
        send_data_list = []
        errors_list = []

        try:
            if clients_list:
                receive_data_list, send_data_list, errors_list = select.select(clients_list, clients_list, [], 0)
        except OSError:
            pass

        for client_with_message in receive_data_list:
            try:
                process_client_message(get_message(client_with_message), messages_deque, client_with_message)
            except Exception:
                LOG.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                clients_list.remove(client_with_message)

        if messages_deque and send_data_list:
            message_data = messages_deque.popleft()
            message = {
                ACTION: MESSAGE,
                SENDER: message_data[0],
                TIME: time.time(),
                MESSAGE_TEXT: message_data[1]
            }

            for waiting_client in send_data_list:
                try:
                    send_message(waiting_client, message)
                except Exception:
                    LOG.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    waiting_client.close()
                    clients_list.remove(waiting_client)


if __name__ == '__main__':
    main()
