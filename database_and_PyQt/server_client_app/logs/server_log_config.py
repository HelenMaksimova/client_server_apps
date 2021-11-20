import logging
from logging import handlers
import sys
import os
import common.variables as variables

LOG_DIRECTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), variables.LOG_DIRECTORY)
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY_PATH, variables.LOG_FILENAME_SERVER)

LOGGER = logging.getLogger('server')
LOGGER.setLevel(logging.DEBUG)

FORMAT = logging.Formatter('%(asctime)-20s %(levelname)-8s %(filename)-10s %(message)s')

STDERR_HANDLER = logging.StreamHandler(sys.stderr)
STDERR_HANDLER.setLevel(logging.INFO)
STDERR_HANDLER.setFormatter(FORMAT)

FILE_HANDLER = handlers.TimedRotatingFileHandler(LOG_FILE_PATH, 'D', 1, encoding='utf-8')
FILE_HANDLER.setLevel(logging.DEBUG)
FILE_HANDLER.setFormatter(FORMAT)

LOGGER.addHandler(STDERR_HANDLER)
LOGGER.addHandler(FILE_HANDLER)

if __name__ == '__main__':
    LOGGER.debug('DEBUG')
    LOGGER.info('INFO')
    LOGGER.warning('WARNING')
    LOGGER.error('ERROR')
    LOGGER.critical('CRITICAL')
