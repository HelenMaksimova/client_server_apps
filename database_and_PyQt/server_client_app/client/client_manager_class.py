import argparse
import logging

from common.descriptors import Port, IpAddress
import common.variables as vrs
from common.metaclasses import ClientVerifier

LOG = logging.getLogger('client')


class ClientManager(metaclass=ClientVerifier):

    server_port = Port()
    server_address = IpAddress()

    def __init__(self):
        self.server_port, self.server_address, self.client_name = self.get_params()

    def get_params(self):
        """
        Метод получения параметров при запуске из комадной строки
        :return: кортеж параметров
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('port', nargs='?', type=int, default=vrs.DEFAULT_PORT)
        parser.add_argument('address', nargs='?', type=str, default=vrs.DEFAULT_IP_ADDRESS)
        parser.add_argument('-n', '--name', type=str, default='')

        args = parser.parse_args()

        server_port = args.port
        server_address = args.address
        client_name = args.name

        return server_port, server_address, client_name

    def run(self):
        pass
