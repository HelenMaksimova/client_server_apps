"""
Модуль дескрипторов
"""


import ipaddress

import common.custom_exceptions as custom_exceptions


class Port:
    """
    Дескриптор для значения атрибута порта.
    В случае, если задаётся значение вне заданного диапазона целых числ,
    выбрасывается исключение.
    """

    def __init__(self, server_port=True):
        self.server_port = server_port

    def __set__(self, instance, value):
        start_value = 0 if self.server_port else 1024
        if not (start_value < value < 65535 and isinstance(value, int)):
            raise custom_exceptions.PortOutOfRange
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def __set_name__(self, owner, name):
        self.name = name


class IpAddress:
    """
    Дескриптор для значения атрибута ip-адреса.
    В случае, если задаётся недопустимое значение, выбрасывается исключение.
    """

    def __set__(self, instance, value):
        if value:
            try:
                ipaddress.ip_address(value)
            except ValueError:
                raise custom_exceptions.IpAddressError
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __delete__(self, instance):
        del instance.__dict__[self.name]

    def __set_name__(self, owner, name):
        self.name = name


