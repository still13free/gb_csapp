import argparse
import socket
import sys
import select
import threading
import time
import logging
import logs.server_log_config

from common.variables import *
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ServerMaker
from db.server_db import ServerDB

LOGGER = logging.getLogger('server')


@log
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    def init_socket(self):
        LOGGER.info(f'Launched server, port for connections: {self.port}. '
                    f'Listen address - {self.addr} (if not specified - any).')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        transport.bind((self.addr, self.port))
        transport.settimeout(1)
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_client_message(self, message, client):
        LOGGER.debug(f'Processing message from {client.getpeername()}: {message}.')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            u_name = message[USER][ACCOUNT_NAME]
            if u_name not in self.names.keys():
                self.names[u_name] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(u_name, client_ip, client_port)
                send_message(client, RESPONSE_OK)
            else:
                response = RESPONSE_ERR
                response[ERROR] = 'This username already exists!'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            del u_name
            return

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message \
                and DESTINATION in message and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            u_name = message[ACCOUNT_NAME]
            self.database.user_logout(u_name)
            self.clients.remove(self.names[u_name])
            self.names[u_name].close()
            del self.names[u_name]
            del u_name
            return

        response = RESPONSE_ERR
        response[ERROR] = 'Bad request.'
        send_message(client, response)
        return

    def process_message(self, message, listen_socks):
        user_from = message[SENDER]
        user_to = message[DESTINATION]
        if user_to in self.names and self.names[user_to] in listen_socks:
            send_message(self.names[user_to], message)
            LOGGER.info(f'Message sent from "{user_from}" to "{user_to}"')
        elif user_to in self.names and self.names[user_to] not in listen_socks:
            raise ConnectionError
        else:
            text = f'User "{user_to}" not registered on server.'
            LOGGER.error(text)
            service_message = {
                ACTION: MESSAGE,
                SENDER: 'server',
                DESTINATION: user_from,
                TIME: time.time(),
                MESSAGE_TEXT: text,
            }
            send_message(self.names[user_from], service_message)
            del text
            del service_message

    def run(self):
        self.init_socket()

        while True:
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
                    to_recv_list, to_send_list, err_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if to_recv_list:
                for sender in to_recv_list:
                    try:
                        message = get_message(sender)
                        self.process_client_message(message, sender)
                        LOGGER.info(f'Message received: {message}.')
                        del message
                    except Exception:
                        LOGGER.info(f'Client {sender.getpeername()} disconnected.')
                        self.clients.remove(sender)

            for msg in self.messages:
                try:
                    self.process_message(msg, to_send_list)
                except Exception:
                    u_name = msg[DESTINATION]
                    LOGGER.info(f'Connection with user "{u_name}" lost.')
                    self.clients.remove(self.names[u_name])
                    del self.names[u_name]
                    del u_name
            self.messages.clear()


def print_help():
    print('Supported commands:'
          '\n\t - !h OR help - print this help'
          '\n\t - !u OR users - print list of users on server'
          '\n\t - !a OR all - print list of all known users'
          '\n\t - !l OR loghist - print login history'
          '\n\t - !x OR exit - shutdown server')


def main_server():
    listen_address, listen_port = parse_args()

    database = ServerDB()

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    print('Messenger server. Ready to work!')
    print_help()
    while True:
        command = input('Enter command: ')
        if command == '!h' or command == 'help':
            print_help()
        elif command == '!u' or command == 'users':
            for user in sorted(database.active_users_list()):
                print(f"User '{user[0]}' from {user[1]}:{user[2]} has established connection in {user[3]}")
        elif command == '!a' or command == 'all':
            for user in sorted(database.users_list()):
                print(f"User '{user[0]}' last login at {user[1]}")
        elif command == '!l' or command == 'loghist':
            name = input('Enter username or leave blank to see all: ')
            for user in sorted(database.login_history(name)):
                print(f"User: '{user[0]}'. Login at: {user[1]}. From: {user[2]}:{user[3]}")
        elif command == '!x' or command == 'exit':
            print('Shutdown server.')
            time.sleep(1)
            break
        else:
            print('Unknown command. Enter "!h" OR "help" without quotes to get supported commands.')


if __name__ == '__main__':
    main_server()
