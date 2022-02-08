import logging
from datetime import datetime

DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'

PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'

LOGGING_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s %(levelname)-8s %(filename)s %(message)s'
LOG_DATE = datetime.now().date()
LOG_NOW = datetime.now  # !ВАЖНО! функция

RESPONSE_OK = {RESPONSE: 200}
RESPONSE_ERR = {RESPONSE: 400, ERROR: 'Bad Request'}

MODE_LISTEN = 'listen'
MODE_SEND = 'send'
