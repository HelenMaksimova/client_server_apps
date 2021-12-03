import sys

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QTimer
import configparser


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
        self.setFixedSize(800, 600)
        self.setWindowTitle('Сервер сообщений - alpha')

        exit_btn = QAction('Выход', self)
        exit_btn.setShortcut('Ctrl+Q')
        exit_btn.triggered.connect(qApp.quit)

        self.renew_btn = QAction('Обновить список', self)
        self.settings_btn = QAction('Настройки сервера', self)
        self.history_btn = QAction('История клиентов', self)

        self.menuBar().addActions([exit_btn, self.renew_btn, self.settings_btn, self.history_btn])

        label = QLabel('Список подключённых клиентов:', self)
        label.setFixedSize(250, 16)
        label.move(10, 30)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 50)
        self.active_clients_table.setFixedSize(780, 500)

        self.statusBar()


class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(700, 650)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(300, 600)
        self.close_button.clicked.connect(self.hide)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(680, 580)


class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        self.setFixedSize(365, 260)
        self.setWindowTitle('Настройки сервера')

        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(275, 28)
        self.db_path_select.clicked.connect(self.open_file_dialog)

        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel('С какого IP принимаем соединения:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(190, 220)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.hide)

    def open_file_dialog(self):
        self.dialog = QFileDialog(self)
        path = self.dialog.getExistingDirectory()
        self.db_path.insert(path)


class ServerGuiManager:

    def __init__(self, database, new_connection, config=None):
        self.app = QApplication(sys.argv)
        self.database = database
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

        self.main_window.history_btn.triggered.connect(self.show_history_window)
        self.main_window.renew_btn.triggered.connect(self.renew_users_list)
        self.main_window.settings_btn.triggered.connect(self.show_settings_window)

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

    def renew_users_list(self):
        if self.new_connection.value:
            self.table_model.fill_from_db()
            self.main_window.active_clients_table.resizeColumnsToContents()
            with self.new_connection.locker:
                self.new_connection.value = False

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
