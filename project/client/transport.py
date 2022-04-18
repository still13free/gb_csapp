import json
import socket
import time
import threading
import hashlib
import hmac
import binascii
import logging
import project.logs.config_client_log

from PyQt5.QtCore import pyqtSignal, QObject
from project.common.utils import *
from project.common.variables import *
from project.common.errors import ServerError

LOGGER = logging.getLogger('client')
SOCKET_LOCK = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """
    Класс, реализующий транспортную подсистему клиентского модуля.
    Отвечает за взаимодействие с сервером.
    """
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, ip, port, database, username, password, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password = password
        self.transport = None
        self.keys = keys
        self.connection_init(ip, port)

        try:
            self.users_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                self.critical_raise_server_error()
            LOGGER.error('Connection timeout while updating users lists.')
            LOGGER.error('Истекло время соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            self.critical_raise_server_error()
        self.running = True

    def connection_init(self, ip, port):
        """Метод-установщик соединения с сервером."""
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            LOGGER.info(f'Connection attempt №{i + 1}')
            LOGGER.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)
        if not connected:
            self.critical_raise_server_error('Failed to establish server connection.',
                                             'Не удалось установить соединение с сервером!')

        LOGGER.debug('Server connection established.')
        LOGGER.debug('Установлено соединение с сервером.')

        password_bytes = self.password.encode(ENCODING)
        salt = self.username.lower().encode(ENCODING)
        password_hash = hashlib.pbkdf2_hmac('sha512', password_bytes, salt, 5130)
        password_hash_string = binascii.hexlify(password_hash)
        pubkey = self.keys.publickey().export_key().decode('ascii')

        with SOCKET_LOCK:
            presence = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey,
                },
            }
            try:
                send_message(self.transport, presence)
                answer = get_message(self.transport)
                if RESPONSE in answer:
                    if answer[RESPONSE] == 400:
                        raise ServerError(answer[ERROR])
                    elif answer[RESPONSE] == 511:
                        answer_data = answer[DATA]
                        hashkey = hmac.new(password_hash_string, answer_data.encode(ENCODING))
                        digest = hashkey.digest()
                        my_answer = RESPONSE_511
                        my_answer[DATA] = binascii.b2a_base64(digest).decode('ascii')
                        send_message(self.transport, my_answer)
                        self.process_server_answer(get_message(self.transport))
            except (OSError, json.JSONDecodeError):
                raise ServerError('Сбой соединения в процессе авторизации.')

    def process_server_answer(self, message):
        """Метод-обработчик принимаемых сообщений сервера."""
        LOGGER.debug(f'Processing message from server: {message}.')
        LOGGER.debug(f'Рабзор сообщения от сервера: {message}.')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(message[ERROR])
            elif message[RESPONSE] == 205:
                self.users_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                LOGGER.error(f'Received unknown verification code: {message[RESPONSE]}.')
                LOGGER.error(f'Принят неизвестный код подтверждения {message[RESPONSE]}.')
        elif ACTION in message and message[ACTION] == MESSAGE and MESSAGE_TEXT in message \
                and SENDER in message and DESTINATION in message and message[DESTINATION] == self.username:
            LOGGER.info(f"Received message from user '{message[SENDER]}': {message[MESSAGE_TEXT]}")
            LOGGER.info(f"Получено сообщение от пользователя '{message[SENDER]}':{message[MESSAGE_TEXT]}")
            self.new_message.emit(message)

    def users_list_update(self):
        """Метод-запрос с сервера списка всех пользователей."""
        LOGGER.debug('Request for a list of registered users.')
        LOGGER.debug('Запрос списка зарегестрированных на сервере пользователей.')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
        }
        with SOCKET_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.database.add_users(answer[LIST_INFO])
        else:
            LOGGER.error('Failed to update active users list.')
            LOGGER.error('Не удалось обновить список пользователей.')

    def contacts_list_update(self):
        """Метод-запрос с сервера списка контактов текущего пользователя."""
        self.database.clear_contacts()
        LOGGER.debug(f"Request for a contact list of '{self.username}'.")
        LOGGER.debug(f"Запрос списка контактов для пользователя '{self.username}'.")
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username,
        }
        with SOCKET_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOGGER.error('Failed to update contact list.')
            LOGGER.error('Не удалось обновить список контактов.')

    def add_contact(self, contact):
        """Метод-оповещение сервера о добавлении другого пользователя в список контактов."""
        LOGGER.debug(f"Adding contact '{contact}'.")
        LOGGER.debug(f"Добавление контакта '{contact}'.")
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with SOCKET_LOCK:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))

    def del_contact(self, contact):
        """Метод-оповещение сервера об удалении другого пользователя из списка контактов."""
        LOGGER.debug(f"Deleting contact '{contact}'.")
        LOGGER.debug(f"Удаление контакта '{contact}'.")
        req = {
            ACTION: DEL_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with SOCKET_LOCK:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))

    def key_request(self, user):
        """Метод-запрос с сервера публичного ключа другого пользователя."""
        LOGGER.debug(f"Request for public key of user '{user}'.")
        LOGGER.debug(f"Запрос публичного ключа пользователя '{user}'.")
        req = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user,
        }
        with SOCKET_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 511:
            return answer[DATA]
        else:
            LOGGER.error(f"Failed to get public key of user '{user}'.")
            LOGGER.error(f"Не удалось получить ключ собеседника '{user}'.")

    def send_message(self, contact, text):
        """Метод-отправщик сообщений другим пользователям."""
        message = {
            ACTION: MESSAGE,
            TIME: time.time(),
            SENDER: self.username,
            DESTINATION: contact,
            MESSAGE_TEXT: text,
        }
        with SOCKET_LOCK:
            send_message(self.transport, message)
            self.process_server_answer(get_message(self.transport))
            LOGGER.info(f"Message sent to user '{contact}': {text}")
            LOGGER.info(f"Отправлено сообщение пользователю '{contact}':{text}")

    def shutdown(self):
        """Метод-оповещение сервера о завершении работы клиента."""
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
        }
        with SOCKET_LOCK:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        LOGGER.info('The transport is shutting down')
        LOGGER.info('Завершение работы транспорта.')
        time.sleep(0.5)

    def run(self):
        """Метод, описывающий основной цикл работы транспортного потока."""
        LOGGER.debug('Запущен поток приёма сообщений от сервера.')
        LOGGER.debug('The thread for receiving messages from the server is started.')
        while self.running:
            time.sleep(1)
            message = None
            with SOCKET_LOCK:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        self.critical_connection_lost()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    self.critical_connection_lost()
                finally:
                    self.transport.settimeout(5)
            if message:
                self.process_server_answer(message)

    def critical_connection_lost(self):
        LOGGER.critical('Server connection lost.')
        LOGGER.critical('Связь с сервером потеряна.')
        self.running = False
        self.connection_lost.emit()

    @staticmethod
    def critical_raise_server_error(log_text='Server connection lost.', err_text='Соединение с сервером потеряно!'):
        LOGGER.critical(log_text)
        LOGGER.critical(err_text)
        raise ServerError(err_text)
