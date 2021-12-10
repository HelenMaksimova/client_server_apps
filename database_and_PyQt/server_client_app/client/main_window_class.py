"""
Модуль основных GUI-классов
"""


import base64

from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, qApp, QApplication, QMessageBox
from client.dialog_window_classes import AddContactDialog, DelContactDialog
from client.ui import main_window
import common.variables as vrs


class HistoryModel(QStandardItemModel):
    """
    Класс модели истории сообщений
    """

    def __init__(self, database):
        """
        Метод инициализации
        """
        super().__init__()
        self.database = database

    def update_model(self, username):
        """
        Метод обновления модели
        """
        self.clear()
        data = self.database.get_user_history(username)
        data.sort(key=lambda x: x[3], reverse=True)
        for item in data[:20][::-1]:
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(230, 230, 255)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(228, 242, 255)))
                self.appendRow(mess)


class ContactsModel(QStandardItemModel):
    """
    Класс модели списка контактов пользователя
    """

    def __init__(self, database):
        """
        Метод инициализации
        """
        super().__init__()
        self.database = database

    def update_model(self):
        """
        Метод обновления модели
        """
        self.clear()
        data = (QStandardItem(item) for item in self.database.get_contacts())
        for row in data:
            self.appendRow(row)


class MainWindow(QMainWindow):
    """
    Класс основного окна приложения клиента
    """

    def __init__(self, client, database):
        """
        Метод инициализации. Задаются основные параметры
        (объект бэк-энда - client, объект базы данных, объекты шифровки и дешифровки и т.д.).
        Устанавливаются модели, создаются объекты дополнительных окон, назначаются обработчики событий для элементов,
        выполняется подключение слотов к внешним объектам. После чего окно отображается.
        """
        super().__init__()
        self.ui = main_window.Ui_MainWindow()
        self.ui.setupUi(self)

        self.client = client
        self.database = database
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.decrypter = PKCS1_OAEP.new(client.keys)

        self.contacts_model = ContactsModel(self.database)
        self.history_model = HistoryModel(self.database)

        self.ui.contacts_list.setModel(self.contacts_model)
        self.ui.history_list.setModel(self.history_model)

        self.contacts_model.update_model()

        self.add_contact_dialog = AddContactDialog(self.database, self.client)
        self.del_contact_dialog = DelContactDialog(self.database, self.client)

        self.ui.add_contact_point.triggered.connect(self.add_contact_dialog.show)
        self.ui.del_contact_point.triggered.connect(self.del_contact_dialog.show)
        self.ui.exit_point.triggered.connect(self.close)
        self.ui.add_contact_btn.clicked.connect(self.add_contact_dialog.show)
        self.ui.del_contact_btn.clicked.connect(self.del_contact_dialog.show)
        self.ui.clear_text_area_btn.clicked.connect(self.ui.message_text_area.clear)
        self.ui.send_message_btn.clicked.connect(self.send_message)
        self.ui.contacts_list.doubleClicked.connect(self.set_current_chat)

        self.messages = QMessageBox()

        self.change_to_disabled()

        self.make_connection(self.client, self.add_contact_dialog, self.del_contact_dialog)

        self.show()

    def change_to_disabled(self):
        """
        Метод изменения доступности элементов (на недоступные)
        """
        self.history_model.clear()
        self.ui.history_label.setText('История сообщений')
        self.ui.message_label.setText('Дважды кликните на получателе в окне контактов.')
        self.ui.message_text_area.setDisabled(True)
        self.ui.send_message_btn.setDisabled(True)
        self.ui.clear_text_area_btn.setDisabled(True)

    def change_to_enabled(self):
        """
        Метод изменения доступности элементов (на доступные)
        """
        self.ui.message_label.setText('Введите сообщение')
        self.ui.message_text_area.setDisabled(False)
        self.ui.send_message_btn.setDisabled(False)
        self.ui.clear_text_area_btn.setDisabled(False)

    def send_message(self):
        """
        Метод отправки сообщений (с шифрованием)
        """
        message_text = self.ui.message_text_area.toPlainText()
        self.ui.message_text_area.clear()
        if message_text:
            message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf8'))
            message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
            try:
                self.client.send_message_to_server(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            except (ConnectionResetError, ConnectionAbortedError):
                self.close()
            else:
                self.database.save_message('out', self.current_chat, message_text)
                self.history_model.update_model(self.current_chat)

    def set_current_chat(self):
        """
        Метод установки текущего чата по выделенному элементу в списке контактов
        """
        self.current_chat = self.ui.contacts_list.currentIndex().data()
        self.select_contact()

    def select_contact(self):
        """
        Метод установки текущего чата
        """
        self.ui.history_label.setText(f'История сообщений с {self.current_chat}')
        self.history_model.update_model(self.current_chat)
        self.change_to_enabled()
        self.current_chat_key = self.client.get_user_pubkey(self.current_chat)
        if self.current_chat_key:
            self.encryptor = PKCS1_OAEP.new(
                RSA.import_key(self.current_chat_key))

    @pyqtSlot(dict)
    def message(self, message):
        """
        Метод-слот при получении сообщения (с дешифровкой)
        """
        sender = message[vrs.SENDER]
        encrypted_message = base64.b64decode(message[vrs.MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(
                self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return
        self.database.save_message('in', self.current_chat, decrypted_message.decode('utf8'))
        if sender == self.current_chat:
            self.history_model.update_model(self.current_chat)
        else:
            if self.database.check_contact(sender):
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.select_contact()
            else:
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.'
                                          f'\n Данного пользователя нет в вашем контакт-листе.'
                                          f'\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.client.add_contact(sender)
                    self.database.add_contact(sender)
                    self.contacts_model.update_model()
                    self.current_chat = sender
                    self.select_contact()

    @pyqtSlot()
    def connection_lost(self):
        """
        Метод-слот при потере соединения с сервером
        """
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    @pyqtSlot()
    def contacts_changed(self):
        """
        Метод-слот при изменении списка контактов
        """
        self.contacts_model.update_model()

    @pyqtSlot()
    def sig_205(self):
        """
        Метод-слот при изменении списка пользователей на сервере
        """
        if self.current_chat and not self.database.check_user(
                self.current_chat):
            self.messages.warning(
                self,
                'Сочувствую',
                'К сожалению собеседник был удалён с сервера.')
            self.change_to_disabled()
            self.current_chat = None
        self.contacts_model.update_model()

    def make_connection(self, client_obj, contact_add_obj, contact_del_obj):
        """
        Метод установки соединения между методами-слотами и сигналами внешних объектов
        """
        client_obj.new_message.connect(self.message)
        client_obj.connection_lost.connect(self.connection_lost)
        client_obj.message_205.connect(self.sig_205)
        contact_add_obj.contacts_changed.connect(self.contacts_changed)
        contact_del_obj.contacts_changed.connect(self.contacts_changed)
