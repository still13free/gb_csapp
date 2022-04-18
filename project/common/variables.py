import logging

LOGGING_LEVEL = logging.DEBUG  # Текущий уровень логирования
LOG_FORMAT = '%(asctime)s %(levelname)-8s %(filename)s %(message)s'  # Формат строки логирования

DEFAULT_PORT = 7777  # Порт по умолчанию для сетевого ваимодействия
DEFAULT_IP_ADDRESS = '127.0.0.1'  # IP-адрес по умолчанию для подключения клиента
MAX_CONNECTIONS = 5  # Максимальная очередь подключений
MAX_PACKAGE_LENGTH = 1024  # Максимальная длина сообщения в байтах
ENCODING = 'utf-8'  # Кодировка проекта
SERVER_CONFIG = 'server.ini'  # Файл конфигурации серверной базы данных

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
ADD_CONTACT = 'add'
DEL_CONTACT = 'del'
USERS_REQUEST = 'get_users'
PUBLIC_KEY_REQUEST = 'pubkey_need'

# Словари-ответы:
RESPONSE_200 = {
    RESPONSE: 200,
}
RESPONSE_202 = {
    RESPONSE: 202,
    LIST_INFO: None,
}
RESPONSE_205 = {
    RESPONSE: 205,
}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None,
}
RESPONSE_511 = {
    RESPONSE: 511,
    DATA: None,
}

# Переменные для unit-тестов:
TEST_TIME = 5.13
TEST_USER = 'test_user'
TEST_RESPONSE_200 = {
    RESPONSE: 200,
}
TEST_RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: 'Bad request',
}
