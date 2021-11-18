"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»).
При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().

2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса. По результатам проверки должно выводиться
соответствующее сообщение.

3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). Таблица должна состоять из двух колонок.
"""

import subprocess
import ipaddress
import socket
import re
import tabulate
from typing import List


def ping_process(address: str) -> bool:
    """
    Функция для проверки доступности ip-адреса.
    Использует утилиту ping с ключами на количество и время ожидания ответа.
    Возвращает True, если адрес доступен, иначе возвращает False
    :param address: ip-адресс или имя хоста (строка)
    :return: True, если адрес доступен, иначе возвращает False
    """
    pattern = re.compile(r', (\d+) received')
    try:
        ip_address = ipaddress.ip_address(socket.gethostbyname(address))
    except socket.gaierror:
        return False
    args = ['ping', '-c', '1', '-W', '2', str(ip_address)]
    ping_result_subproc = subprocess.Popen(args, stdout=subprocess.PIPE)
    ping_result_row = ping_result_subproc.stdout.readlines()[-2].decode()
    return bool(int(re.findall(pattern, ping_result_row)[-1]))


def host_ping(addresses: List[str]):
    """
    Функция для проверки доступности ip-адресов (или имен хостов).
    Выводит в консоль соответствующую информацию в формате <адрес> <доступность>
    :param addresses: список ip-адрессов или имён хостов (список строк)
    :return: None
    """
    for address in addresses:
        print(address, 'Узел доступен' if ping_process(address) else 'Узел недоступен')


def host_range_ping(start_address: str, end_address: str):
    """
    Функция для проверки доступности ip-адресов в заданном диапазоне.
    Выводит в консоль соответствующую информацию в формате <адрес> <доступность>
    :param start_address: адрес начала диапазона
    :param end_address: адрес конца диапазона
    :return: None
    """
    start_ip_address = ipaddress.ip_address(start_address)
    end_ip_address = ipaddress.ip_address(end_address)
    address_list = [str(start_ip_address + item) for item in range(int(end_ip_address) - int(start_ip_address) + 1)]
    host_ping(address_list)


def host_range_ping_tab(start_address: str, end_address: str):
    """
    Функция для проверки доступности ip-адресов в заданном диапазоне.
    Выводит в консоль соответствующую информацию в формате таблицы из двух столбцов: reachable и unreachable
    :param start_address: адрес начала диапазона
    :param end_address: адрес конца диапазона
    :return:
    """
    start_ip_address = ipaddress.ip_address(start_address)
    end_ip_address = ipaddress.ip_address(end_address)
    address_list = [str(start_ip_address + item) for item in range(int(end_ip_address) - int(start_ip_address) + 1)]
    result_dict = {
        'reachable': [],
        'unreachable': [],
    }
    for address in address_list:
        print(f'Идёт проверка адреса {address}...')
        if ping_process(address):
            result_dict['reachable'].append(address)
        else:
            result_dict['unreachable'].append(address)
    print('\n', tabulate.tabulate(result_dict, headers='keys', tablefmt='pipe'), sep='')


if __name__ == '__main__':

    print('*******************************\n', 'Работа функции host_ping:', sep='')
    host_ping(['yandex.ru', '198.167.0.1', '198.167.0.6'])
    print('*******************************\n')

    print('*******************************\n', 'Работа функции host_range_ping:', sep='')
    host_range_ping('198.167.0.1', '198.167.0.6')
    print('*******************************\n')

    print('*******************************\n', 'Работа функции host_range_ping_tab:', sep='')
    host_range_ping_tab('198.167.0.1', '198.167.0.6')
    print('*******************************\n')
