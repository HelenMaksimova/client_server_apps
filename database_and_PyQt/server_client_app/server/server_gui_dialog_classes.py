"""
Модуль дополнительный GUI-классов сервера
"""


from PyQt5.QtWidgets import QDialog, QPushButton, QTableView, QLabel, QLineEdit, QFileDialog, QMessageBox, QComboBox


class HistoryWindow(QDialog):
    """
    Класс окна истории соббщений
    """

    def __init__(self):
        """
        Метод инициализации
        """
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        """
        Метод создания элементов
        """
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(700, 650)

        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(300, 600)
        self.close_button.clicked.connect(self.hide)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(680, 580)


class ConfigWindow(QDialog):
    """
    Класс окна конфигурации сервера
    """

    def __init__(self):
        """
        Метод инициализации
        """
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        """
        Метод создания элементов
        """
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
        """
        Метод-обработчик для отображения окна выбора файла
        """
        self.dialog = QFileDialog(self)
        path = self.dialog.getExistingDirectory()
        self.db_path.insert(path)


class RegisterUser(QDialog):
    """
    Класс окна регистрации пользователя
    """

    def __init__(self):
        """
        Метод инициализации
        """
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        """
        Метод создания элементов
        """
        self.setWindowTitle('Регистрация')
        self.setFixedSize(175, 183)
        self.setModal(True)

        self.label_username = QLabel('Введите имя пользователя:', self)
        self.label_username.move(10, 10)
        self.label_username.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel('Введите пароль:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.label_conf = QLabel('Введите подтверждение:', self)
        self.label_conf.move(10, 100)
        self.label_conf.setFixedSize(150, 15)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Сохранить', self)
        self.btn_ok.move(10, 150)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.hide)

        self.messages = QMessageBox()


class DelUserDialog(QDialog):
    """
    Класс окна удаления пользователя
    """

    def __init__(self):
        """
        Метод инициализации
        """
        super().__init__()
        self.create_widgets()

    def create_widgets(self):
        """
        Метод создания элементов
        """
        self.setFixedSize(350, 120)
        self.setWindowTitle('Удаление пользователя')
        self.setModal(True)

        self.selector_label = QLabel(
            'Выберите пользователя для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.hide)
