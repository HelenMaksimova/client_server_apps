import datetime

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, qApp, QApplication, QMessageBox
from PyQt5 import uic
import sys
from client.dialog_window_classes import AddContactDialog, DelContactDialog
from client.ui import main_window


class HistoryModel(QStandardItemModel):

    def __init__(self, database):
        super().__init__()
        self.database = database

    def update_model(self, username):
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
    def __init__(self, database):
        super().__init__()
        self.database = database

    def update_model(self):
        self.clear()
        data = (QStandardItem(item) for item in self.database.get_contacts())
        for row in data:
            self.appendRow(row)


class MainWindow(QMainWindow):

    def __init__(self, client, database):
        super().__init__()
        self.ui = main_window.Ui_MainWindow()
        self.ui.setupUi(self)

        self.client = client
        self.database = database
        self.current_chat = None

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
        self.history_model.clear()
        self.ui.message_label.setText('Дважды кликните на получателе в окне контактов.')
        self.ui.message_text_area.setDisabled(True)
        self.ui.send_message_btn.setDisabled(True)
        self.ui.clear_text_area_btn.setDisabled(True)

    def change_to_enabled(self):
        self.ui.message_label.setText('Введите сообщение')
        self.ui.message_text_area.setDisabled(False)
        self.ui.send_message_btn.setDisabled(False)
        self.ui.clear_text_area_btn.setDisabled(False)

    def send_message(self):
        message_text = self.ui.message_text_area.toPlainText()
        self.ui.message_text_area.clear()
        if message_text:
            try:
                self.client.send_message_to_server(self.current_chat, message_text)
            except (ConnectionResetError, ConnectionAbortedError):
                self.close()
            else:
                self.history_model.update_model(self.current_chat)

    def set_current_chat(self):
        self.current_chat = self.ui.contacts_list.currentIndex().data()
        self.select_contact()

    def select_contact(self):
        self.ui.history_label.setText(f'История сообщений с {self.current_chat}')
        self.history_model.update_model(self.current_chat)
        self.change_to_enabled()

    @pyqtSlot(str)
    def message(self, sender):
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
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    @pyqtSlot()
    def contacts_changed(self):
        self.contacts_model.update_model()

    def make_connection(self, client_obj, contact_add_obj, contact_del_obj):
        client_obj.new_message.connect(self.message)
        client_obj.connection_lost.connect(self.connection_lost)
        contact_add_obj.contacts_changed.connect(self.contacts_changed)
        contact_del_obj.contacts_changed.connect(self.contacts_changed)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(1, 2)
    window.start_dialog.show()
    sys.exit(app.exec_())
