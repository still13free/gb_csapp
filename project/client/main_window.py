from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import json
import logging
import base64

from project.common.errors import ServerError
from project.common.variables import *
from project.client.contacts_add import AddContactDialog
from project.client.contacts_del import DelContactDialog
from project.ui.client_main_window import Ui_mainWindow

LOGGER = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """Класс, реализующий основное пользовательское окно."""

    def __init__(self, database, transport, keys):
        super().__init__()

        self.database = database
        self.transport = transport
        self.decrypter = PKCS1_OAEP.new(keys)

        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        self.ui.sendButton.clicked.connect(self.send_message)  # кнопка отправки сообщения
        self.ui.addButton.clicked.connect(self.contacts_add_dialog_show)  # кнопка добавления контакта
        self.ui.actionAddContact.triggered.connect(self.contacts_add_dialog_show)  # меню добавления контакта
        self.ui.delButton.clicked.connect(self.contacts_del_dialog_show)  # кнопка удаления контакта
        self.ui.actionDelContact.triggered.connect(self.contacts_del_dialog_show)  # меню удаления контакта
        self.ui.list_contacts.doubleClicked.connect(self.active_contact_select)  # выбор активного диалога

        self.messages = QMessageBox()
        self.contacts_model = None
        self.history_model = None
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None

        self.make_connection()
        self.disable_message_field()
        self.contacts_list_update()
        self.show()

    def history_list_update(self):
        """
        Метод, обновляющий содержимое list_history(QListView).
        Заполняет соответствующий элемент историей переписки с текущим контактом.
        """
        history = sorted(self.database.get_history(self.current_chat),
                         key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_history.setModel(self.history_model)
        self.history_model.clear()

        length = len(history)
        start_index = 0
        if length > 20:
            start_index = length - 20

        for i in range(start_index, length):
            row = history[i]
            if row[1] == 'in':
                msg = QStandardItem(f'{row[0]} ({row[3].replace(microsesond=0)}):\n {row[2]}')
                msg.setEditable(False)
                msg.setTextAlignment(Qt.AlignLeft)
                msg.setBackground(QBrush(QColor(255, 191, 191)))
                self.history_model.appendRow(msg)
            else:
                msg = QStandardItem(f'Вы ({row[3].replace(microsesond=0)}):\n {row[2]}')
                msg.setEditable(False)
                msg.setTextAlignment(Qt.AlignRight)
                msg.setBackground(QBrush(QColor(255, 191, 191)))
                self.history_model.appendRow(msg)
        self.ui.list_history.scrollToBottom()

    def contacts_list_update(self):
        """
        Метод, обновляющий содержимое list_contacts(QListView).
        Заполняет соответствующий элемент списком контактов.
        """
        contacts = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def contacts_add_dialog_show(self):
        """Метод, создающий диалоговое окно добавления контакта."""
        global add_dialog
        add_dialog = AddContactDialog(self.transport, self.database)
        add_dialog.ui.buttonBox.accepted.connect(
            lambda: self.contacts_add_dialog_confirm(add_dialog)
        )
        add_dialog.show()

    def contacts_add_dialog_confirm(self, dialog_window):
        """Метод-обработчик нажатия кнопки добавления контакта."""
        new_contact = dialog_window.ui.comboBox.currentText()
        self.contacts_add(new_contact)
        dialog_window.close()

    def contacts_add(self, new_contact):
        """
        Метод, добавляющий контакт в базы данных сервера и клиента.
        После добавления также обновляет содержимое окна.
        """
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера!', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Критическая ошибка!', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка!', 'Истекло время ожидания ответа от сервера.')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            LOGGER.info(f"Contact '{new_contact.text()}' was added successfully.")
            LOGGER.info(f"Контакт '{new_contact.text()}' был успешно добавлен.")
            self.messages.information(self, 'Уведомление', f"Контакт '{new_contact.text()}' был успешно добавлен.")

    def contacts_del_dialog_show(self):
        """Метод, создающий диалоговое окно удаления контакта."""
        global del_dialog
        del_dialog = DelContactDialog(self.database)
        del_dialog.ui.buttonBox.accepted.connect(
            lambda: self.contacts_del_dialog_confirm(del_dialog)
        )
        del_dialog.show()

    def contacts_del_dialog_confirm(self, dialog_window):
        """Метод-обработчик нажатия кнопки удаления контакта."""
        contact = dialog_window.ui.comboBox.currentText()
        self.contacts_del(contact)
        dialog_window.close()

    def contacts_del(self, contact):
        """
        Метод, удаляющий контакт из баз данных сервера и клиента.
        После удаления также обновляет содержимое окна.
        """
        try:
            self.transport.del_contact(contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера!', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Критическая ошибка!', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка!', 'Истекло время ожидания ответа от сервера.')
        else:
            self.database.del_contact(contact)
            self.contacts_list_update()
            LOGGER.info(f"Contact '{contact.text()}' was deleted successfully.")
            LOGGER.info(f"Контакт '{contact.text()}' был успешно удалён.")
            self.messages.information(self, 'Уведомление', f"Контакт '{contact.text()}' был успешно удалён.")
            if contact == self.current_chat:
                self.current_chat = None
                self.disable_message_field()

    def active_contact_select(self):
        """Метод-обработчик двойного нажатия по списку контактов."""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.active_contact_set()

    def active_contact_set(self):
        """Метод, активирующий чат с выбранным контактом."""
        try:
            self.current_chat_key = self.transport.key_request(self.current_chat)
            LOGGER.debug(f"Received a public key for contact '{self.current_chat}'.")
            LOGGER.debug(f"Получен открытый ключ для контакта '{self.current_chat}'.")
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            LOGGER.debug(f"Failed to get public key for contact '{self.current_chat}'.")
            LOGGER.debug(f"Не удалось получить открытый ключ для контакта '{self.current_chat}'.")

        if not self.current_chat_key:
            self.messages.warning(self, 'Внимание!', 'Для выбранного пользователя отсутствует ключ шифрования.')
            return

        # self.ui.label_message.setText('enable')
        self.ui.message_field.setEnabled(True)
        self.ui.sendButton.setDisabled(False)
        self.ui.clearButton.setEnabled(True)

        self.history_list_update()

    def disable_message_field(self):
        """Метод, деактивирующий поле ввода сообщения и сопутствующие кнопки."""
        # self.ui.label_message.setText('disable')
        self.ui.message_field.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.message_field.setDisabled(True)
        self.ui.sendButton.setDisabled(True)
        self.ui.clearButton.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def send_message(self):
        """
        Функция отправки сообщения.
        Осуществляет шифрование сообщения и его отправку текущему собеседнику.
        """
        message_text = self.ui.message_field.toPlainText()
        self.ui.message_field.clear()
        if not message_text:
            return

        message_text_encrypted = self.encryptor.encrypt(message_text.encode(ENCODING))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
        try:
            self.transport.send_message(self.current_chat,
                                        message_text_encrypted_base64.decode('ascii'))
        except ServerError as err:
            self.messages.critical(self, 'Ошибка!', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Критическая ошибка!', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка!', 'Истекло время ожидания ответа от сервера.')
        except (ConnectionAbortedError, ConnectionResetError):
            self.messages.critical(self, 'Критическая ошибка!', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.log_message(self.current_chat, 'out', message_text)
            self.history_list_update()

    # slots to signals
    @pyqtSlot(dict)
    def new_message(self, message):
        """
        Слот-обработчик поступившего сообщения.
        Дешифрует сообщения и сохраняет их в базе данных.
        Если сообщение пришло не от текущего собеседника, запрашивает действие пользователя.
        """
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(self, 'Ошибка!', 'Не удалось декодировать сообщение.')
            return

        sender = message[SENDER]
        self.database.log_message(sender, 'in', decrypted_message.decode(ENCODING))
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if self.messages.question(
                        self,
                        'Новое сообщение!',
                        f"Получено новое сообщение от пользователя '{sender}'."
                        f"\nХотите открыть чат с ним?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                ) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.active_contact_set()
            else:
                if self.messages.question(
                        self,
                        'Новое сообщение!',
                        f"Принято сообщение от пользователя вне списка контактов '{sender}'."
                        f"\nХотите добавить в контакты и открыть чат с ним?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                ) == QMessageBox.Yes:
                    self.contacts_add(sender)
                    self.current_chat = sender
                    self.active_contact_set()

    @pyqtSlot()
    def sig_205(self):
        """Слот, обновляющий базу данных по требованию сервера."""
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(
                self,
                'Внимание!',
                'К сожалению, текущий собеседник был удалён с сервера.'
            )
            self.disable_message_field()
        self.contacts_list_update()

    @pyqtSlot()
    def connection_lost(self):
        """Слот-обработчик потери соединения с сервером."""
        self.messages.critical(
            self,
            'Сбой соединения!',
            'Потеряно соединение с сервером.'
            '\nПрограмма будет завершена.'
        )
        self.close()

    def make_connection(self):
        """Метод, соединяющий сигналы и слоты."""
        self.transport.new_message.connect(self.new_message)
        self.transport.message_205.connect(self.sig_205)
        self.transport.connection_lost.connect(self.connection_lost)
