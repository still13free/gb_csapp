import json
import socket
import sys
import time
import threading
import hashlib
import hmac
import binascii
import logging
import project.logs.client_log_config

from PyQt5.QtCore import pyqtSignal, QObject
from project.common.utils import *
from project.common.variables import *
from project.common.errors import ServerError

LOGGER = logging.getLogger('client')
SOCK_LOCK = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, ip_address, port, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password = passwd

        self.transport = None
        self.keys = keys
        self.connection_init(ip_address, port)

        try:
            self.users_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                self.critical_raise_server_error()
            LOGGER.error('Connection timeout while updating users lists.')
        except json.JSONDecodeError:
            self.critical_raise_server_error()
        self.running = True

    @staticmethod
    def critical_raise_server_error(log_text='Server connection lost.', err_text='Соединение с сервером потеряно!'):
        LOGGER.critical(log_text)
        raise ServerError(err_text)

    def critical_connection_lost(self):
        LOGGER.critical('Server connection lost.')
        self.running = False
        self.connection_lost.emit()

    def connection_init(self, ip, port):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            LOGGER.info(f'Connection attempt №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                LOGGER.debug('Server connection established.')
                break
            time.sleep(1)

        if not connected:
            self.critical_raise_server_error('Failed to establish server connection.',
                                             'Не удалось установить соединение с сервером!')

        LOGGER.debug('Start auth dialog.')
        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        LOGGER.debug(f'Password hash ready: {passwd_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with SOCK_LOCK:
            presence = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey,
                },
            }
            LOGGER.debug(f"Presence message: {presence}")

            try:
                send_message(self.transport, presence)
                ans = get_message(self.transport)
                LOGGER.debug(f'Server response = {ans}.')
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        ans_data = ans[DATA]
                        hashkey = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hashkey.digest()
                        my_ans = RESPONSE_NAR
                        my_ans[DATA] = binascii.b2a_base64(digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_answer(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                LOGGER.debug(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')

    def process_server_answer(self, message):
        LOGGER.debug(f'Processing message from server: {message}.')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.users_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                LOGGER.error(f'Received unknown verification code: {message[RESPONSE]}')

        elif ACTION in message and message[ACTION] == MESSAGE and MESSAGE_TEXT in message \
                and SENDER in message and DESTINATION in message and message[DESTINATION] == self.username:
            LOGGER.debug(f"Received message from user '{message[SENDER]}': {message[MESSAGE_TEXT]}")
            self.new_message.emit(message)

    def key_request(self, user):
        LOGGER.debug(f'Public key request for {user}')
        req = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with SOCK_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 511:
            return answer[DATA]
        else:
            LOGGER.error(f'Failed to get buddy public key for {user}.')

    def users_list_update(self):
        LOGGER.debug(f'Users list request by {self.username}.')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
        }
        LOGGER.debug(f'Request generated: {req}.')
        with SOCK_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        LOGGER.debug(f'Answer received: {answer}.')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.database.add_users(answer[LIST_INFO])
        else:
            LOGGER.error('Failed to update active users list.')

    def contacts_list_update(self):
        LOGGER.debug(f'Contacts list request for user {self.username}.')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username,
        }
        LOGGER.debug(f'Request generated: {req}.')
        with SOCK_LOCK:
            send_message(self.transport, req)
            answer = get_message(self.transport)
        LOGGER.debug(f'Answer received: {answer}.')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOGGER.error('Failed to update contacts list.')

    def add_contact(self, contact):
        LOGGER.debug(f"Creating contact '{contact}'.")
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with SOCK_LOCK:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))

    def del_contact(self, contact):
        LOGGER.debug(f"Deleting contact '{contact}'.")
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with SOCK_LOCK:
            send_message(self.transport, req)
            self.process_server_answer(get_message(self.transport))

    def send_message(self, user_to, message):
        message_to_send = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: user_to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Message created: {message_to_send}')
        with SOCK_LOCK:
            send_message(self.transport, message_to_send)
            self.process_server_answer(get_message(self.transport))
            LOGGER.info(f"Message sent to '{user_to}'")

    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with SOCK_LOCK:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        LOGGER.debug('Transport shutdown.')
        time.sleep(1)

    def run(self):
        LOGGER.debug('Process running.')
        while self.running:
            time.sleep(1)
            message = None
            with SOCK_LOCK:
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
                LOGGER.debug(f'Received message from server: {message}')
                self.process_server_answer(message)
