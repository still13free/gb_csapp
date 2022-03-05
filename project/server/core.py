import binascii
import hmac
import json
import select
import socket
import threading
import os
import logging

# from project.common.decorators import login_required
from project.common.descriptors import Port
from project.common.utils import send_message, get_message
from project.common.variables import *

LOGGER = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.sock = None
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True
        self.names = dict()

        super().__init__()

    def run(self):
        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                LOGGER.info(f'Connection established with {client_address}.')
                self.clients.append(client)

            to_recv_list = []
            to_send_list = []
            err_list = []

            try:
                if self.clients:
                    to_recv_list, self.listen_sockets, self.error_sockets = \
                        select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                LOGGER.error(f'Sockets error: {err}')

            if to_recv_list:
                for sender in to_recv_list:
                    try:
                        message = get_message(sender)
                        self.process_client_message(message, sender)
                        del message
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        LOGGER.debug(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(sender)

    def init_socket(self):
        LOGGER.info(f'Launched server, port for connections: {self.port}. '
                    f'Listen address - {self.addr} (if not specified - any).')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def remove_client(self, client):
        LOGGER.info(f'Client {client.getpeername()} disconnected.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def process_message(self, message):
        user_from = message[SENDER]
        user_to = message[DESTINATION]

        if user_to in self.names and self.names[user_to] in self.listen_sockets:
            try:
                send_message(self.names[user_to], message)
                LOGGER.info(f'Message sent from "{user_from}" to "{user_to}"')
            except OSError:
                self.remove_client(user_to)
        elif user_to in self.names and self.names[user_to] not in self.listen_sockets:
            LOGGER.error(f"Connection with user '{user_to}' lost.")
            self.remove_client(self.names[user_to])
        else:
            LOGGER.error(f"User '{user_to}' not registered on server.")

    def process_client_message(self, message, client):
        LOGGER.debug(f'Processing message from {client.getpeername()}: {message}.')

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            self.authorize_user(message, client)

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and DESTINATION in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_OK)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_ERR
                response[ERROR] = 'User not registered on server.'
                try:
                    send_message(client, response)
                except OSError:
                    pass

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.remove_client(client)

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_ACP
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_ACP
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_OK)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.del_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_OK)
            except OSError:
                self.remove_client(client)

        elif ACTION in message and message[ACTION] == PUBLIC_KEY_REQUEST and ACCOUNT_NAME in message:
            response = RESPONSE_NAR
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            if not response[DATA]:
                response = RESPONSE_ERR
                response[ERROR] = 'Non public key for current user.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)
        else:
            response = RESPONSE_ERR
            response[ERROR] = 'Bad request.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def authorize_user(self, message, sock):
        LOGGER.debug(f'Start auth process for {message[USER]}')

        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_ERR
            response[ERROR] = 'Имя пользователя уже занято.'
            try:
                LOGGER.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                LOGGER.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()

        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_ERR
            response[ERROR] = 'Пользователь не зарегистрирован.'
            try:
                LOGGER.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            LOGGER.debug('Correct username, starting passwd check.')

            message_auth = RESPONSE_NAR
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, 'MD5')
            digest = hash.digest()
            LOGGER.debug(f'Auth message = {message_auth}')
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                LOGGER.debug('Auth error, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])

            if RESPONSE in ans and ans[RESPONSE] == 511 and hmac.compare_digest(digest, client_digest):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_OK)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY])
            else:
                response = RESPONSE_ERR
                response[ERROR] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_RST)
            except OSError:
                self.remove_client(self.names[client])
