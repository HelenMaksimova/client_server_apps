from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QDialog, qApp
import sys
from client.ui import add_contact, del_contact, input_name


class AvailibleContactsModel(QStandardItemModel):
    def __init__(self, database):
        super().__init__()
        self.database = database

    def update_model(self):
        self.clear()
        users = set(self.database.get_users()) - set(self.database.get_contacts())
        users.remove(self.database.username)
        data = (QStandardItem(item) for item in users)
        for row in data:
            self.appendRow(row)


class InputUsernameDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = input_name.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.press_ok)
        self.ok_pressed = False
        self.show()

    def press_ok(self):
        username = self.ui.user_login.text()
        password = self.ui.user_password.text()
        if username and password:
            self.ok_pressed = True
            qApp.exit(0)


class AddContactDialog(QDialog):

    contacts_changed = pyqtSignal()

    def __init__(self, database, client):
        super().__init__()
        self.ui = add_contact.Ui_Dialog()
        self.ui.setupUi(self)
        self.database = database
        self.client = client
        self.availible_contacts_model = AvailibleContactsModel(database)
        self.ui.comboBox.setModel(self.availible_contacts_model)
        self.ui.pushButton.clicked.connect(self.update_userlist)
        self.ui.buttonBox.accepted.connect(self.add_contact)

    def showEvent(self, event):
        self.availible_contacts_model.update_model()

    def update_userlist(self):
        self.client.user_list_update()
        self.availible_contacts_model.update_model()

    def add_contact(self):
        contact = self.ui.comboBox.currentText()
        if contact:
            self.client.add_contact(contact)
            self.database.add_contact(contact)
            self.contacts_changed.emit()


class DelContactDialog(QDialog):

    contacts_changed = pyqtSignal()

    def __init__(self, database, client):
        super().__init__()
        self.ui = del_contact.Ui_Dialog()
        self.ui.setupUi(self)
        self.database = database
        self.client = client
        self.contacts_model = QStandardItemModel()
        self.ui.comboBox.setModel(self.contacts_model)
        self.ui.buttonBox.accepted.connect(self.delete_contact)

    def showEvent(self, event):
        self.update_contacts()

    def update_contacts(self):
        self.contacts_model.clear()
        users = self.database.get_contacts()
        for user in users:
            self.contacts_model.appendRow(QStandardItem(user))

    def delete_contact(self):
        contact = self.ui.comboBox.currentText()
        if contact:
            self.client.remove_contact(contact)
            self.database.del_contact(contact)
            self.contacts_changed.emit()
