"""Константы"""

# Порт поумолчанию для сетевого ваимодействия

DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# Название базы данных
DATABASE_SERVER = 'sqlite:///server_base.db3'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
PORT = 'port'
SENDER = 'sender'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
EXIT = 'exit'
DESTINATION = 'destination'
RESPONDEFAULT_IP_ADDRESSSE = 'respondefault_ip_addressse'

# логирование
LOG_DIRECTORY = 'data'
LOG_FILENAME_CLIENT = 'client.log'
LOG_FILENAME_SERVER = 'server.log'
