"""Программа-клиент"""

import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, PORT, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_message
import argparse
import logs.client_log_config
import logging
import custom_exceptions
from decos import Log


LOG = logging.getLogger('client')
CLIENT_MODES = {
    'send': 'отправка сообщений',
    'listen': 'приём сообщений',
}


@Log(LOG)
def create_message(action=PRESENCE, message=None, port=DEFAULT_PORT, acc_name='Guest'):
    """
    Функция генерирует запрос о присутствии клиента
    :param action: тип передаваемого сообщения
    :param message: текст сообщения
    :param acc_name: логин (имя аккауната)
    :param port: порт клиента
    :return: сообщение-запрос о присутствии клиента (словарь)
    """
    result_message = {
        ACTION: action,
        TIME: time.time(),
        PORT: port,
        USER: {
            ACCOUNT_NAME: acc_name
        }
    }
    if message and action == MESSAGE:
        result_message[MESSAGE_TEXT] = message
    return result_message


@Log(LOG)
def input_message(client_socket):
    """
    Функция для ввода сообщения пользователем
    :param client_socket: объект сокета клиента
    :return: сообщение (строка)
    """
    while True:
        message = input('Введите сообщение для отправки (для выхода введите exit):')
        if message.strip():
            break
        else:
            print('Сообщение не может быть пустым!')
    if message == 'exit':
        client_socket.close()
        exit(0)
    return message


@Log(LOG)
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


@Log(LOG)
def message_from_server(server_message):
    """
    Функция - обработчик сообщений других пользователей, поступающих с сервера
    :param server_message: сообщение от сервера
    """
    if ACTION in server_message and server_message[ACTION] == MESSAGE and SENDER in server_message \
            and MESSAGE_TEXT in server_message:
        print(f'Получено сообщение от пользователя {server_message[SENDER]}:\n{server_message[MESSAGE_TEXT]}')
        LOG.info(f'Получено сообщение от пользователя {server_message[SENDER]}:\n{server_message[MESSAGE_TEXT]}')
    else:
        LOG.error(f'Получено некорректное сообщение с сервера: {server_message}')


@Log(LOG)
def mainloop(client_mode, transport, server_address, server_port):
    """
    Функция основной петли отправки-получения сообщений
    :param client_mode: режим клиента
    :param transport: сокет
    :param server_address: адрес сервера
    :param server_port: порт сервера
    """
    print(f'Режим работы - {CLIENT_MODES[client_mode]}')
    while True:
        try:
            if client_mode == 'send':
                message = create_message(MESSAGE, input_message(transport), server_port)
                send_message(transport, message)
                LOG.info(f'Отправлено сообщение {message[MESSAGE_TEXT]} '
                         f'от пользователя {message[USER][ACCOUNT_NAME]}')
            elif client_mode == 'listen':
                message_from_server(get_message(transport))
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            LOG.error(f'Соединение с сервером {server_address} было потеряно.')
            sys.exit(1)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, default=DEFAULT_PORT)
    parser.add_argument('address', nargs='?', type=str, default=DEFAULT_IP_ADDRESS)
    parser.add_argument('-m', '--mode', type=str, default='send')

    args = parser.parse_args()

    server_port = args.port
    server_address = args.address
    client_mode = args.mode

    try:
        if not(1024 < server_port < 65535):
            raise custom_exceptions.PortOutOfRange
        if client_mode not in CLIENT_MODES:
            raise custom_exceptions.ClientModeError
    except custom_exceptions.PortOutOfRange as error:
        LOG.critical(f'Ошибка порта {server_port}: {error}. Соединение закрывается.')
        sys.exit(1)
    except custom_exceptions.ClientModeError as error:
        LOG.critical(f'Ошибка режима запуска {server_port}: {error}. Соединение закрывается.')
        sys.exit(1)

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_message(port=server_port)
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
    except ConnectionRefusedError:
        LOG.critical(f'Не удалось подключиться к серверу {server_address}:{server_port}')
        sys.exit(1)
    else:
        mainloop(client_mode, transport, server_address, server_port)


if __name__ == '__main__':
    main()
