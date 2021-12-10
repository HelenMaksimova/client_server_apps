import argparse
import logging
import os
import sys

from Cryptodome.PublicKey import RSA

from client.client_classes import Client
from client.client_storage_class import ClientStorage
from client.main_window_class import MainWindow
from common.descriptors import Port, IpAddress
import common.variables as vrs
from common.metaclasses import ClientVerifier
from client.dialog_window_classes import InputUsernameDialog
from PyQt5.QtWidgets import QApplication

LOG = logging.getLogger('client')


class ClientManager:

    server_port = Port()
    server_address = IpAddress()

    def __init__(self):
        self.server_port, self.server_address, self.client_name = self.get_params()
        self.password = None

    def get_keys(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        key_file = os.path.join(dir_path, f'{self.client_name}.key')
        if not os.path.exists(key_file):
            keys = RSA.generate(2048, os.urandom)
            with open(key_file, 'wb') as key:
                key.write(keys.export_key())
        else:
            with open(key_file, 'rb') as key:
                keys = RSA.import_key(key.read())
        return keys

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
        app = QApplication(sys.argv)

        dialog = InputUsernameDialog()
        if self.client_name:
            dialog.ui.user_login.setText(self.client_name)
        app.exec_()
        if dialog.ok_pressed:
            self.client_name = dialog.ui.user_login.text()
            self.password = dialog.ui.user_password.text()
            del dialog
        else:
            exit(0)

        database = ClientStorage(self.client_name)

        keys = self.get_keys()

        client = Client(self.client_name, self.password, database, self.server_address, self.server_port, keys)
        client.setDaemon(True)
        if client.connection:
            client.start()

            main_window = MainWindow(client, database)
            main_window.setWindowTitle(f'Чат Программа alpha release - {self.client_name}')
            app.exec_()

            client.client_shutdown()
            client.join()
        else:
            exit(0)

