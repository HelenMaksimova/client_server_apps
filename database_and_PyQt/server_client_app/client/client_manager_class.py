import argparse
import logging
import sys

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

        if not self.client_name:
            dialog = InputUsernameDialog()
            app.exec_()
            if dialog.ok_pressed:
                self.client_name = dialog.ui.lineEdit.text()
                del dialog
            else:
                exit(0)

        database = ClientStorage(self.client_name)

        client = Client(self.client_name, database, self.server_address, self.server_port)
        client.setDaemon(True)
        client.start()

        main_window = MainWindow(client, database)
        main_window.setWindowTitle(f'Чат Программа alpha release - {self.client_name}')
        app.exec_()

        client.client_shutdown()
        client.join()

