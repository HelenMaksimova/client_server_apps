"""
Модуль второстепенных GUI-классов
"""


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QDialog, qApp
import sys
from client.ui import add_contact, del_contact, input_name


class AvailibleContactsModel(QStandardItemModel):
    """
    Класс модели доступных для добавления контактов
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
        users = set(self.database.get_users()) - set(self.database.get_contacts())
        users.remove(self.database.username)
        data = (QStandardItem(item) for item in users)
        for row in data:
            self.appendRow(row)


class InputUsernameDialog(QDialog):
    """
    Класс стартового окна приложения с формой ввода логина и пароля
    """

    def __init__(self):
        """
        Метод инициализации
        """
        super().__init__()
        self.ui = input_name.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.press_ok)
        self.ok_pressed = False
        self.show()

    def press_ok(self):
        """
        Метод-обработчик нажатия кнопки ОК. Проверяет заполненность полей формы.
        """
        username = self.ui.user_login.text()
        password = self.ui.user_password.text()
        if username and password:
            self.ok_pressed = True
            qApp.exit(0)


class AddContactDialog(QDialog):
    """
    Класс окна добавления контакта
    """

    contacts_changed = pyqtSignal()

    def __init__(self, database, client):
        """
        Метод инициализации
        """
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
        """
        Метод, обновляющий модель списка пользователей при показе окна
        """
        self.availible_contacts_model.update_model()

    def update_userlist(self):
        """
        Метод-обработчик для обновления списка пользователей
        """
        self.client.user_list_update()
        self.availible_contacts_model.update_model()

    def add_contact(self):
        """
        Метод-обработчик для добавления контакта
        """
        contact = self.ui.comboBox.currentText()
        if contact:
            self.client.add_contact(contact)
            self.database.add_contact(contact)
            self.contacts_changed.emit()


class DelContactDialog(QDialog):
    """
    Класс окна удаления контакта
    """

    contacts_changed = pyqtSignal()

    def __init__(self, database, client):
        """
        Метод инициализации
        """
        super().__init__()
        self.ui = del_contact.Ui_Dialog()
        self.ui.setupUi(self)
        self.database = database
        self.client = client
        self.contacts_model = QStandardItemModel()
        self.ui.comboBox.setModel(self.contacts_model)
        self.ui.buttonBox.accepted.connect(self.delete_contact)

    def showEvent(self, event):
        """
        Метод, обновляющий список контактов пользователя при показе окна
        """
        self.update_contacts()

    def update_contacts(self):
        """
        Метод обновления списка контактов пользователя
        """
        self.contacts_model.clear()
        users = self.database.get_contacts()
        for user in users:
            self.contacts_model.appendRow(QStandardItem(user))

    def delete_contact(self):
        """
        Метод-обработчик для удаления контакта
        """
        contact = self.ui.comboBox.currentText()
        if contact:
            self.client.remove_contact(contact)
            self.database.del_contact(contact)
            self.contacts_changed.emit()
