class PortOutOfRange(Exception):
    def __str__(self):
        return 'В качестве порта может быть указано только число в диапазоне от 1024 до 65535'


class NoResponseInServerMessage(Exception):
    def __str__(self):
        return 'Получено некорректное сообщение от сервера (отсутствует поле "response")'


class IncorrectData(Exception):
    def __str__(self):
        return 'Получены некорректные данные'


class ClientModeError(Exception):
    def __str__(self):
        return 'Киент запущен с недопустимым режимом выполнения'
