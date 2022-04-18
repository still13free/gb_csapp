from PyQt5.QtWidgets import qApp, QMessageBox, QApplication, QDialog

from project.ui.client_start_dialog import Ui_authDialog


class AuthDialog(QDialog):
    """
    Класс-аутентификатор, реализующий диалоговое окно с запросом логина и пароля пользователя.
    """
    def __init__(self):
        super().__init__()

        self.startMainApp = False
        self.messages = QMessageBox()

        self.ui = Ui_authDialog()
        self.ui.setupUi(self)
        self.show()

    def accept(self) -> None:
        if not self.ui.nickname.text():
            self.messages.warning(self, 'Внимание!', 'Отсутствует никнейм!')
        elif not self.ui.password.text():
            self.messages.warning(self, 'Внимание!', 'Пароль не введён!')
        else:
            self.startMainApp = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = AuthDialog()
    app.exec_()
