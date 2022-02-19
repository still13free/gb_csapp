import os
import sys
import logging

from common.variables import LOGGING_LEVEL, LOG_FORMAT

FORMATTER = logging.Formatter(LOG_FORMAT)

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

LOG_FILE = logging.FileHandler(PATH, encoding='utf-8')
LOG_FILE.setFormatter(FORMATTER)

LOG_STREAM = logging.StreamHandler(sys.stderr)
LOG_STREAM.setFormatter(FORMATTER)
LOG_STREAM.setLevel(logging.ERROR)

logger = logging.getLogger('client')
logger.addHandler(LOG_FILE)
logger.addHandler(LOG_STREAM)
logger.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    logger.debug('debug information')
    logger.info('information message')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical error')
