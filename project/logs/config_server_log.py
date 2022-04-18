import os
import sys
import logging
import logging.handlers

from project.common.variables import LOGGING_LEVEL, LOG_FORMAT

FORMATTER = logging.Formatter(LOG_FORMAT)

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')

LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='D')
LOG_FILE.setFormatter(FORMATTER)

LOG_STREAM = logging.StreamHandler(sys.stderr)
LOG_STREAM.setFormatter(FORMATTER)
LOG_STREAM.setLevel(logging.ERROR)

logger = logging.getLogger('server')
logger.addHandler(LOG_FILE)
logger.addHandler(LOG_STREAM)
logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    logger.debug('debug information')
    logger.info('information message')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical error')
