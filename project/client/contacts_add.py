import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from project.ui.client_contacts_add_dialog import Ui_addContactDialog

LOGGER = logging.getLogger('client')


class AddContactDialog(QDialog):
    """
    Диалоговое окно добавления другого пользователя в список контактов.
    Предоставляет текущему пользователю возможность добавить незнакомые контакты из общего списка в свой.
    """

    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.ui = Ui_addContactDialog()
        self.ui.setupUi(self)
        self.ui.refreshButton.clicked.connect(self.refresh_possible_contacts)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.update_possible_contacts()

    def update_possible_contacts(self):
        """
        Метод, заполняющий список возможных контактов.
        Создаёт список из всех зарегистрированных пользователей, за исключением уже добавленных и самого себя.
        """
        self.ui.comboBox.clear()
        all_users_list = set(self.database.get_users())  # множество всех пользователей
        contacts_list = set(self.database.get_contacts())  # множество контактов текущего пользователя

        all_users_list.remove(self.transport.username)  # удаляем текущего пользователя из общего списка
        self.ui.comboBox.addItems(all_users_list - contacts_list)  # формируем и добавляем список возможных контактов

    def refresh_possible_contacts(self):
        """
        Метод, обновляющий список возможных контактов.
        Запрашивает с сервера список известных пользователей и обновляет содержимое окна.
        """
        try:
            self.transport.users_list_update()
        except OSError:
            pass
        else:
            self.update_possible_contacts()
            LOGGER.debug('The list of possible contacts has been updated successfully!')
            LOGGER.debug('Обноление списка возможных контактов выполнено успешно!')
