import binascii
import hashlib
import sys

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
import configparser

from server.server_gui_dialog_classes import HistoryWindow, ConfigWindow, RegisterUser, DelUserDialog


class UsersListModel(QStandardItemModel):

    fields = ['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения']

    def __init__(self, database=None):
        super().__init__()
        self.setHorizontalHeaderLabels(self.fields)
        self.database = database

    def fill_model(self, data):
        self.clear()
        self.setHorizontalHeaderLabels(self.fields)
        for row in data:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            self.appendRow([user, ip, port, time])

    def fill_from_db(self):
        if self.database:
            data = self.database.users_active()
            self.fill_model(data)


class HistoryListModel(QStandardItemModel):
    fields = ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено']

    def __init__(self, database=None):
        super().__init__()
        self.setHorizontalHeaderLabels(self.fields)
        self.database = database

    def fill_model(self, data):
        self.clear()
        self.setHorizontalHeaderLabels(self.fields)
        for row in data:
            user, last_seen, sent, received = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            received = QStandardItem(str(received))
            received.setEditable(False)
            self.appendRow([user, last_seen, sent, received])

    def fill_from_db(self):
        if self.database:
            data = self.database.message_history()
            self.fill_model(data)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        self.setFixedSize(850, 600)
        self.setWindowTitle('Сервер сообщений - alpha')

        exit_btn = QAction('Выход', self)
        exit_btn.setShortcut('Ctrl+Q')
        exit_btn.triggered.connect(qApp.quit)

        self.renew_btn = QAction('Обновить список', self)
        self.settings_btn = QAction('Настройки сервера', self)
        self.history_btn = QAction('История клиентов', self)
        self.add_user_btn = QAction('Зарегистрировать клиента', self)
        self.del_user_btn = QAction('Удалить клиента', self)

        actions = [
            exit_btn,
            self.renew_btn,
            self.settings_btn,
            self.history_btn,
            self.add_user_btn,
            self.del_user_btn
        ]

        self.menuBar().addActions(actions)

        label = QLabel('Список подключённых клиентов:', self)
        label.setFixedSize(250, 16)
        label.move(10, 30)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 50)
        self.active_clients_table.setFixedSize(830, 500)

        self.statusBar()


class ServerGuiManager:

    def __init__(self, database, new_connection, server, config=None):
        self.app = QApplication(sys.argv)
        self.database = database
        self.server = server
        self.new_connection = new_connection
        self.create_widgets()
        self.config = config if config else configparser.ConfigParser()
        self.timer = QTimer()

    def create_widgets(self):
        self.main_window = MainWindow()
        self.table_model = UsersListModel(self.database)
        self.main_window.active_clients_table.setModel(self.table_model)
        self.main_window.active_clients_table.resizeColumnsToContents()

        self.history_window = HistoryWindow()
        self.history_model = HistoryListModel(self.database)
        self.history_window.history_table.setModel(self.history_model)
        self.history_window.history_table.resizeColumnsToContents()

        self.config_window = ConfigWindow()

        self.add_user_window = RegisterUser()
        self.add_user_window.btn_ok.clicked.connect(self.save_data)

        self.del_user_window = DelUserDialog()
        self.del_user_window.btn_ok.clicked.connect(self.remove_user)

        self.main_window.history_btn.triggered.connect(self.show_history_window)
        self.main_window.renew_btn.triggered.connect(self.renew_users_list)
        self.main_window.settings_btn.triggered.connect(self.show_settings_window)
        self.main_window.add_user_btn.triggered.connect(self.show_add_user_window)
        self.main_window.del_user_btn.triggered.connect(self.show_del_user_window)

        self.config_window.save_btn.clicked.connect(self.save_server_settings)

    def show_main_window(self):
        self.table_model.fill_from_db()
        self.main_window.active_clients_table.resizeColumnsToContents()
        self.main_window.statusBar().showMessage('Сервер работает')
        self.main_window.show()

    def show_history_window(self):
        self.history_model.fill_from_db()
        self.history_window.history_table.resizeColumnsToContents()
        self.history_window.show()

    def show_settings_window(self):
        self.config_window.show()

    def show_add_user_window(self):
        self.add_user_window.client_name.clear()
        self.add_user_window.client_passwd.clear()
        self.add_user_window.client_conf.clear()
        self.add_user_window.show()

    def show_del_user_window(self):
        self.all_users_fill()
        self.del_user_window.show()

    def renew_users_list(self):
        if self.new_connection.value:
            self.table_model.fill_from_db()
            self.main_window.active_clients_table.resizeColumnsToContents()
            with self.new_connection.locker:
                self.new_connection.value = False

    def all_users_fill(self):
        self.del_user_window.selector.clear()
        self.del_user_window.selector.addItems([item[0] for item in self.database.users_all()])

    def remove_user(self):
        self.database.remove_user(self.del_user_window.selector.currentText())
        if self.del_user_window.selector.currentText() in self.server.clients_names:
            sock = self.server.clients_names[self.del_user_window.selector.currentText()]
            del self.server.clients_names[self.del_user_window.selector.currentText()]
            self.server.remove_client(sock)
        self.server.service_update_lists()
        self.del_user_window.hide()

    def save_data(self):
        if not self.add_user_window.client_name.text():
            self.add_user_window.messages.critical(
                self.add_user_window, 'Ошибка', 'Не указано имя пользователя.')
            return
        elif self.add_user_window.client_passwd.text() != self.add_user_window.client_conf.text():
            self.add_user_window.messages.critical(
                self.add_user_window, 'Ошибка', 'Введённые пароли не совпадают.')
            return
        elif self.database.check_user(self.add_user_window.client_name.text()):
            self.add_user_window.messages.critical(
                self.add_user_window, 'Ошибка', 'Пользователь уже существует.')
            return
        else:
            passwd_bytes = self.add_user_window.client_passwd.text().encode('utf-8')
            salt = self.add_user_window.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac(
                'sha512', passwd_bytes, salt, 10000)
            self.database.add_user(
                self.add_user_window.client_name.text(),
                binascii.hexlify(passwd_hash))
            self.add_user_window.messages.information(
                self.add_user_window, 'Успех', 'Пользователь успешно зарегистрирован.')
            self.server.service_update_lists()
            self.add_user_window.hide()

    def save_server_settings(self):
        message = QMessageBox()
        self.config['SETTINGS']['Database_path'] = self.config_window.db_path.text()
        self.config['SETTINGS']['Database_file'] = self.config_window.db_file.text()
        try:
            port = int(self.config_window.port.text())
        except ValueError:
            message.warning(self.config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            self.config['SETTINGS']['Listen_Address'] = self.config_window.ip.text()
            if 1023 < port < 65536:
                self.config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    self.config.write(conf)
                    message.information(
                        self.config_window, 'OK', 'Настройки успешно сохранены и будут применены приследующем запуске!')
            else:
                message.warning(
                    self.config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    def start_timer(self):
        self.timer.timeout.connect(self.renew_users_list)
        self.timer.start(1000)
