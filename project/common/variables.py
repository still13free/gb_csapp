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

PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'

LOGGING_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s %(levelname)-8s %(filename)s %(message)s'
LOG_DATE = datetime.now().date()
