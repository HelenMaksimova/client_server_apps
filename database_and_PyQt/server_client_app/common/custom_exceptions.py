"""
Модуль исключений
"""


class PortOutOfRange(Exception):
    """
    Класс исключения при значении порта вне диапазона
    """
    def __str__(self):
        return 'В качестве порта может быть указано только число в диапазоне от 1024 (0 для сервера) до 65535'


class NoResponseInServerMessage(Exception):
    """
    Класс исключения при некорректном сообщении сервера
    """
    def __str__(self):
        return 'Получено некорректное сообщение от сервера (отсутствует поле "response")'


class IncorrectData(Exception):
    """
    Класс исключения при некорректных данных
    """
    def __str__(self):
        return 'Получены некорректные данные'


class ClientModeError(Exception):
    """
    Класс исключения при недопустимом режиме выполнения
    """
    def __str__(self):
        return 'Клиент запущен с недопустимым режимом выполнения'


class ConnectInServerSocketError(Exception):
    """
    Класс исключения при недопустимой команде при работе с сокетом сервера
    """
    def __str__(self):
        return 'Обнаружена комманда connect при работе с сокетом сервера'


class NoTCPConnectionError(Exception):
    """
    Класс исключения при отсутствии у сокета настройки по работе с TCP-соединением'
    """
    def __str__(self):
        return 'У сокета отсутствует настройка по работе с TCP-соединением'


class ListenOrAcceptInClientSocketError(Exception):
    """
    Класс исключения при недопустимой команде при работе с сокетом клиента
    """
    def __str__(self):
        return 'Обнаружена комманда listen или команда accept при работе с сокетом клиента'


class SocketInClassAttributesError(Exception):
    """
    Класс исключения при обнаружении в атрибутах класса объекта сокета
    """
    def __str__(self):
        return 'В атрибутах класса обнаружен объект сокета'


class IpAddressError(Exception):
    """
    Класс исключения при некорректном формате ip-адреса
    """
    def __str__(self):
        return 'Некорректный формат ip-адреса'
