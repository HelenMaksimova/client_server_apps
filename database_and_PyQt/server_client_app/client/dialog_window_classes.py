from PyQt5.QtWidgets import QApplication, QDialog
import sys
from ui import add_contact, del_contact, input_name


class InputUsernameDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = input_name.Ui_Dialog()
        self.ui.setupUi(self)


class AddContactDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = add_contact.Ui_Dialog()
        self.ui.setupUi(self)


class DelContactDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.ui = del_contact.Ui_Dialog()
        self.ui.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InputUsernameDialog()
    window.show()
    sys.exit(app.exec_())
