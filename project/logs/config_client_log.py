import os
import sys
import logging

from project.common.variables import LOGGING_LEVEL, LOG_FORMAT

FORMATTER = logging.Formatter(LOG_FORMAT)

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

LOG_FILE = logging.FileHandler(PATH, encoding='utf-8')
LOG_FILE.setFormatter(FORMATTER)

LOG_STREAM = logging.StreamHandler(sys.stderr)
LOG_STREAM.setFormatter(FORMATTER)
LOG_STREAM.setLevel(logging.ERROR)

LOGGER = logging.getLogger('client')
LOGGER.addHandler(LOG_FILE)
LOGGER.addHandler(LOG_STREAM)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.debug('debug information')
    LOGGER.info('information message')
    LOGGER.warning('warning')
    LOGGER.error('error')
    LOGGER.critical('critical error')
