from PyQt5.QtWidgets import QMainWindow, qApp, QApplication
from PyQt5 import uic
import sys
from dialog_window_classes import InputUsernameDialog, AddContactDialog, DelContactDialog


class MainWindow(QMainWindow):

    def __init__(self, client, database):
        super().__init__()
        uic.loadUi('ui/main_window.ui', self)

        self.client = client
        self.database = database

        self.start_dialog = InputUsernameDialog()
        self.add_contact_dialog = AddContactDialog()
        self.del_contact_dialog = DelContactDialog()

        self.start_dialog.ui.buttonBox.accepted.connect(self.open_main_window)
        self.add_contact_point.triggered.connect(self.add_contact_dialog.show)
        self.del_contact_point.triggered.connect(self.del_contact_dialog.show)
        self.add_contact_btn.clicked.connect(self.add_contact_dialog.show)
        self.del_contact_btn.clicked.connect(self.del_contact_dialog.show)
        self.clear_text_area_btn.clicked.connect(self.message_text_area.clear)

    def open_main_window(self):
        username = self.start_dialog.ui.lineEdit.text().strip()
        if username:
            self.show()
        else:
            qApp.exit()

    def fill_contact_list(self):
        pass

    def add_contact(self):
        pass

    def renew_contacts(self):
        pass

    def del_contact(self):
        pass

    def send_message(self):
        pass

    def fill_history(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(1, 2)
    window.start_dialog.show()
    sys.exit(app.exec_())
