"""
Модуль декораторов
"""


import inspect
import logging
import logs.client_log_config
import logs.server_log_config
from functools import wraps


class FilenameFilter(logging.Filter):
    """
    Класс фильтра записей логов для замены имени файла декоратора на имя файла,
    в котором идёт логирование
    """

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def filter(self, record):
        record.filename = self.filename
        return True


class Log:
    """
    Класс для логирования работы функций
    """

    def __init__(self, logger=None):
        """
        Метод инициализации
        :param logger: объект логгера для записи сообщений.
        """
        self.logger = logger

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Обёртка декоратора. Определяется имя функции, из которой была вызвана переданная в декоратор функция, и
            имя модуля.
            Если логгер не определён (self.logger is None), совершается поиск по имени модуля, в котором применён
            декоратор, и загружается или создаётся логгер, в который уходит информационное сообщение о работе функции.
            """
            parent_func_name = inspect.currentframe().f_back.f_code.co_name
            module_name = inspect.currentframe().f_back.f_code.co_filename.split("/")[-1]
            if not self.logger:
                if 'client' in module_name:
                    self.logger = logging.getLogger(f"client_func")
                elif 'server' in module_name:
                    self.logger = logging.getLogger(f"server_func")
                else:
                    self.logger = logging.getLogger()
            self.logger.addFilter(FilenameFilter(module_name))
            self.logger.debug(f'Функция (метод) {func.__name__} вызвана из функции (метода) {parent_func_name} '
                              f'в модуле {module_name} с аргументами:'
                              f'{args}; {kwargs}')
            result = func(*args, **kwargs)
            return result

        return wrapper
