class PortOutOfRange(Exception):
    def __str__(self):
        return 'В качестве порта может быть указано только число в диапазоне от 1024 (0 для сервера) до 65535'


class NoResponseInServerMessage(Exception):
    def __str__(self):
        return 'Получено некорректное сообщение от сервера (отсутствует поле "response")'


class IncorrectData(Exception):
    def __str__(self):
        return 'Получены некорректные данные'


class ClientModeError(Exception):
    def __str__(self):
        return 'Клиент запущен с недопустимым режимом выполнения'


class ConnectInServerSocketError(Exception):
    def __str__(self):
        return 'Обнаружена комманда connect при работе с сокетом сервера'


class NoTCPConnectionError(Exception):
    def __str__(self):
        return 'У сокета отсутствует настройка по работе с TCP-соединением'


class ListenOrAcceptInClientSocketError(Exception):
    def __str__(self):
        return 'Обнаружена комманда listen или команда accept при работе с сокетом клиента'


class SocketInClassAttributesError(Exception):
    def __str__(self):
        return 'В атрибутах класса обнаружен объект сокета'


class IpAddressError(Exception):
    def __str__(self):
        return 'Некорректный формат ip-адреса'
