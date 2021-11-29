import logging
import time

import common.variables as vrs
import custom_exceptions
from common.utils import send_message, get_message

LOG = logging.getLogger('client')


def send_request(sock, request):
    send_message(sock, request)
    answer = get_message(sock)
    LOG.debug(f'Получен ответ {answer}')
    if not (vrs.RESPONSE in answer and answer[vrs.RESPONSE] in (200, 202)):
        raise custom_exceptions.NoResponseInServerMessage
    return answer


def contacts_list_request(sock, name):
    LOG.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        vrs.ACTION: vrs.GET_CONTACTS,
        vrs.TIME: time.time(),
        vrs.USER: name
    }
    LOG.debug(f'Сформирован запрос {req}')
    result = send_request(sock, req)
    return result[vrs.LIST_INFO]


def add_contact(sock, username, contact):
    LOG.debug(f'Создание контакта {contact}')
    req = {
        vrs.ACTION: vrs.ADD_CONTACT,
        vrs.TIME: time.time(),
        vrs.USER: username,
        vrs.ACCOUNT_NAME: contact
    }
    send_request(sock, req)
    LOG.debug('Удачное создание контакта.')


def user_list_request(sock, username):
    LOG.debug(f'Запрос списка известных пользователей {username}')
    req = {
        vrs.ACTION: vrs.USERS_REQUEST,
        vrs.TIME: time.time(),
        vrs.ACCOUNT_NAME: username
    }
    result = send_request(sock, req)
    return result[vrs.LIST_INFO]


def remove_contact(sock, username, contact):
    LOG.debug(f'Создание контакта {contact}')
    req = {
        vrs.ACTION: vrs.REMOVE_CONTACT,
        vrs.TIME: time.time(),
        vrs.USER: username,
        vrs.ACCOUNT_NAME: contact
    }
    send_request(sock, req)
    LOG.debug('Удачное удаление')
