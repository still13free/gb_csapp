import argparse
import json
import socket
import sys
import time
import threading
import logging
import project.logs.client_log_config

from os import system
from project.common.variables import *
from project.common.utils import send_message, get_message
from project.common.errors import RequiredFieldMissingError, IncorrectDataReceivedError, ServerError
from project.common.decorators import log
from project.common.metaclasses import ClientMaker
from project.db.client_db import ClientDB

LOGGER = logging.getLogger('client')

SOCK_LOCK = threading.Lock()
DATABASE_LOCK = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_message(self):
        to_user = input('Enter message recipient: ')
        message = input('Enter message itself: ')

        with DATABASE_LOCK:
            if not self.database.check_user(to_user):
                LOGGER.error(f'Attempting to send message to unregistered recipient: {to_user}')
                return

        message_to_send = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        LOGGER.debug(f'Message created: {message_to_send}')
        with DATABASE_LOCK:
            self.database.log_message(self.account_name, to_user, message)

        with SOCK_LOCK:
            try:
                send_message(self.sock, message_to_send)
                LOGGER.info(f'Message sent to "{to_user}"')
            except OSError as e:
                if e.errno:
                    LOGGER.critical(f'Server connection lost.')
                    exit(1)
                else:
                    LOGGER.error('Failed to send message. Connection timeout.')

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
        }

    def run(self):
        self.print_help()
        while True:
            command = input()
            if command == '!m' or command == 'message':
                self.create_message()
            elif command == '!h' or command == 'help':
                self.print_help()
            elif command == '!c' or command == 'contacts':
                with DATABASE_LOCK:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            elif command == '!e' or command == 'edit':
                self.edit_contacts()
            elif command == '!l' or command == 'history':
                self.print_history()
            elif command == '!x' or command == 'exit':
                with SOCK_LOCK:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except Exception as e:
                        print(e)
                        pass
                print('Shutdown. Thank you for using our service!')
                LOGGER.info('Shutdown by user command.')
                time.sleep(1)
                break
            else:
                print('Unknown command. Enter "!h" OR "help" without quotes to get supported commands.')

    def edit_contacts(self):
        action = input("Enter 'add' to add contact or 'del' to delete contact without quotes: ")
        edit = input("Enter contact's username: ")
        if action == 'del':
            with DATABASE_LOCK:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    LOGGER.error(f'Attempting to delete non-existent contact: {edit}.')
        elif action == 'add':
            if self.database.check_user(edit):
                with DATABASE_LOCK:
                    self.database.add_contact(edit)
                with SOCK_LOCK:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        LOGGER.error('Failed to send information on server.')

    def print_history(self):
        hist_type = input("Enter 'in' - incoming, 'out' - outgoing, or leave blank to see all messages: ")
        with DATABASE_LOCK:
            if hist_type == 'in':
                history_list = self.database.get_history(user_to=self.account_name)
                for message in history_list:
                    print(f'\n<!> Message from {message[0]} at {message[3]}:'
                          f'\n<!> {message[2]}')
            elif hist_type == 'out':
                history_list = self.database.get_history(user_from=self.account_name)
                for message in history_list:
                    print(f'\n<!> Message to {message[1]} at {message[3]}:'
                          f'\n<!> {message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\n<!> Message from {message[0]} to {message[1]} at {message[3]}:'
                          f'\n<!> {message[2]}')

    @staticmethod
    def print_help():
        print('Supported commands:'
              '\n\t - !m OR message - sending message'
              '\n\t - !h OR help - print this help'
              '\n\t - !c OR contacts - print contacts list'
              '\n\t - !e OR edit - edit contacts'
              '\n\t - !l OR history - print messages log'
              '\n\t - !x OR exit - close program'
              )


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            time.sleep(1)
            with SOCK_LOCK:
                try:
                    message = get_message(self.sock)
                except IncorrectDataReceivedError:
                    LOGGER.error(f'Failed to decode received message.')
                except OSError as e:
                    if e.errno:
                        LOGGER.critical(f'Server connection lost.')
                        break
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError, json.JSONDecodeError):
                    LOGGER.critical(f'Server connection lost.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                            and message[DESTINATION] == self.account_name and MESSAGE_TEXT in message:
                        print(f'\nMessage received from user "{message[SENDER]}": {message[MESSAGE_TEXT]}')
                        with DATABASE_LOCK:
                            try:
                                self.database.log_message(message[SENDER], self.account_name, message[MESSAGE_TEXT])
                            except Exception as e:
                                print(e)
                                LOGGER.info('An error occurred while interacting with database.')
                    else:
                        LOGGER.error(f'Received incorrect message from server: {message}.')


@log
def create_presence(account_name):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name,
        },
    }
    LOGGER.debug(f'{PRESENCE}-message generated for user "{account_name}".')
    return out


@log
def process_ans(message):
    LOGGER.debug(f'Processing message from server: {message}.')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400: {message[ERROR]}')
    raise RequiredFieldMissingError(RESPONSE)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Attempting to launch client with wrong port number: {server_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Client terminates.')
        sys.exit(1)
    return server_address, server_port, client_name


def add_contact(sock, username, contact):
    LOGGER.debug(f'Creating contact {contact}.')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Failed to create contact.')
    print('Success!')


def del_contact(sock, username, contact):
    LOGGER.debug(f'Deleting contact {contact}.')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact,
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Failed to delete contact.')
    print('Success!')


def contacts_list_request(sock, name):
    LOGGER.debug(f'Contact list request for user {name}.')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name,
    }
    LOGGER.debug(f'Request generated: {req}.')
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Answer received: {ans}.')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def users_list_request(sock, name):
    LOGGER.debug(f'Users list request by {name}.')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: name,
    }
    LOGGER.debug(f'Request generated: {req}.')
    send_message(sock, req)
    ans = get_message(sock)
    LOGGER.debug(f'Answer received: {ans}.')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


def load_database(sock, database, username):
    try:
        users_list = users_list_request(sock, username)
    except ServerError:
        LOGGER.error('Failed to query known users list.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        LOGGER.error('Failed to query contacts list.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main_client():
    server_address, server_port, client_name = parse_args()

    print('Console messenger. Client module.')
    if not client_name:
        client_name = input('Enter username: ')
    else:
        print(f'Username: {client_name}')
    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, port - {server_port}, username - {client_name}.')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)
        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        LOGGER.info(f'Connection established. Response received from server: {answer}.')
        print(f'Connection established with server.')

    except json.JSONDecodeError:
        LOGGER.error('Failed to decode json-string message.')
        exit(1)

    except ServerError as err:
        LOGGER.error(f'Server returned error while establishing connection: {err.text}.')
        exit(1)

    except RequiredFieldMissingError as err:
        LOGGER.error(f'Required field is missing in server response: {err.missing_field}.')
        exit(1)

    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(f'Failed to connect to server {server_address}:{server_port}. '
                        f'Server refused connection request.')
        exit(1)

    else:
        database = ClientDB(client_name)
        load_database(transport, database, client_name)

        receiver = ClientReader(client_name, transport, database)
        receiver.daemon = True
        receiver.start()

        sender = ClientSender(client_name, transport, database)
        sender.daemon = True
        sender.start()

        LOGGER.debug('Processes running!')

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main_client()
    system('pause')
