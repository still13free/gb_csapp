import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from project.ui.client_contacts_del_dialog import Ui_deleteContactDialog

logger = logging.getLogger('client_dist')


class DelContactDialog(QDialog):
    """
    Диалоговое окно удаления другого пользователя из списка контактов.
    Предоставляет текущему пользователю возможность удалить контакт из собственного списка.
    """

    def __init__(self, database):
        super().__init__()
        self.database = database

        self.ui = Ui_deleteContactDialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.ui.comboBox.addItems(sorted(self.database.get_contacts()))
