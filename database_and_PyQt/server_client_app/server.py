"""Программа-сервер"""
import threading

from server_class import Server, NewConnection
from server_storage_class import ServerStorage
from server_gui_classes import ServerGuiManager

import configparser
import os
import argparse


def get_params(default_port, default_address):
    """
    Метод получения параметров при запуске из комадной строки
    :return: кортеж параметров
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=default_port)
    parser.add_argument('-a', type=str, default=default_address)
    args = parser.parse_args()
    return args.p, args.a


def get_config():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    return config


def main():
    new_connection = NewConnection()

    server_config = get_config()
    listen_port, listen_address = get_params(
        server_config['SETTINGS']['default_port'], server_config['SETTINGS']['listen_address'])

    db_path = os.path.join(server_config['SETTINGS']['Database_path'], server_config['SETTINGS']['Database_file'])

    server = Server(listen_port, listen_address, db_path, new_connection)
    server.daemon = True
    server.start()

    server_manager = ServerGuiManager(server.database, new_connection, server_config)
    server_manager.start_timer()
    server_manager.show_main_window()
    server_manager.app.exec_()


if __name__ == '__main__':
    main()
