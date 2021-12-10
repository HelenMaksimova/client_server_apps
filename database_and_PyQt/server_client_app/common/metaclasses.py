"""
Модуль метаклассов
"""


import dis
from types import FunctionType
from socket import SocketType

import common.custom_exceptions as custom_exceptions


class ServerVerifier(type):
    """
    Метакласс контролирует наличие настройки для подключения по TCP
    и отсутствие использования метода connect в сокете сервера
    на этапе инициализации класса
    """

    def __init__(cls, name, bases, dct):
        methods = [value for key, value in dct.items()
                   if not key.startswith('__') and isinstance(value, FunctionType)]
        tcp_flag = False
        for method in methods:
            for instruction in dis.get_instructions(method):
                if instruction.argrepr == 'SOCK_STREAM':
                    tcp_flag = True
                if instruction.argrepr == 'connect':
                    raise custom_exceptions.ConnectInServerSocketError
        if not tcp_flag:
            raise custom_exceptions.NoTCPConnectionError
        type.__init__(cls, name, bases, dct)


class ClientVerifier(type):
    """
    Метакласс контролирует на этапе инициализации класса наличие настройки для подключения по TCP
    и отсутствие использования методов listen и accept в сокете клиента,
    а также отсутствие в атрибутах класса объектов сокета
    """

    def __init__(cls, name, bases, dct):
        methods = []
        attributes = []
        for key, value in dct.items():
            if not key.startswith('__') and isinstance(value, FunctionType):
                methods.append(value)
            elif not key.startswith('__'):
                attributes.append(value)
        tcp_flag = False
        for attribute in attributes:
            if isinstance(attribute, SocketType):
                raise custom_exceptions.SocketInClassAttributesError
        for method in methods:
            for instruction in dis.get_instructions(method):
                if instruction.argrepr == 'SOCK_STREAM':
                    tcp_flag = True
                if instruction.argrepr in ('listen', 'accept'):
                    raise custom_exceptions.ListenOrAcceptInClientSocketError
        if not tcp_flag:
            raise custom_exceptions.NoTCPConnectionError
        type.__init__(cls, name, bases, dct)
