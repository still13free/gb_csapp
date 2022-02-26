from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp


class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.start_pressed = False  # флаг нажатия кнопки

        self.setWindowTitle('Приветствуем!')
        self.setFixedSize(200, 100)

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(15, 15)
        self.label.setFixedSize(150, 10)

        self.username = QLineEdit(self)
        self.username.setFixedSize(170, 20)
        self.username.move(15, 35)

        self.btn_start = QPushButton('Начать', self)
        self.btn_start.move(15, 65)
        self.btn_start.clicked.connect(self.click)

        self.btn_exit = QPushButton('Выход', self)
        self.btn_exit.move(111, 65)
        self.btn_exit.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.username.text():
            self.start_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
