import logging
import sys
import os
import common.variables as variables

LOG_DIRECTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), variables.LOG_DIRECTORY)
LOG_FILE_PATH = os.path.join(LOG_DIRECTORY_PATH, variables.LOG_FILENAME_CLIENT)

LOGGER = logging.getLogger('client')

LOGGER.setLevel(logging.DEBUG)

FORMAT = logging.Formatter('%(asctime)-20s %(levelname)-8s %(filename)-10s %(message)s')

STDERR_HANDLER = logging.StreamHandler(sys.stderr)
STDERR_HANDLER.setLevel(logging.ERROR)
STDERR_HANDLER.setFormatter(FORMAT)

FILE_HANDLER = logging.FileHandler(LOG_FILE_PATH)
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
