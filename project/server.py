import argparse
import configparser
import os
import socket
import sys
import select
import threading
import time
import logging
import project.logs.server_log_config

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from common.variables import *
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ServerMaker
from db.server_db import ServerDB
from server_gui import *

LOGGER = logging.getLogger('server')
NEW_CONNECTION = False
CONFLAG_LOCK = threading.Lock()


@log
def parse_args(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
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
        self.sock.listen()

    def process_client_message(self, message, client):
        global NEW_CONNECTION
        LOGGER.debug(f'Processing message from {client.getpeername()}: {message}.')

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            u_name = message[USER][ACCOUNT_NAME]
            if u_name not in self.names.keys():
                self.names[u_name] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(u_name, client_ip, client_port)
                send_message(client, RESPONSE_OK)
                with CONFLAG_LOCK:
                    NEW_CONNECTION = True
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
            self.database.process_message(message[SENDER], message[DESTINATION])
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            u_name = message[ACCOUNT_NAME]
            LOGGER.info(f'Client {u_name} correctly disconnected.')
            self.database.user_logout(u_name)
            self.clients.remove(self.names[u_name])
            self.names[u_name].close()
            del self.names[u_name]
            del u_name
            with CONFLAG_LOCK:
                NEW_CONNECTION = True
            return

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_ACP
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_ACP
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_OK)

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message \
                and USER in message and self.names[message[USER]] == client:
            self.database.del_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_OK)

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
            except OSError as err:
                LOGGER.error(f'Sockets error: {err}')

            if to_recv_list:
                for sender in to_recv_list:
                    try:
                        message = get_message(sender)
                        self.process_client_message(message, sender)
                        LOGGER.info(f'Message received: {message}.')
                        del message
                    except OSError:
                        LOGGER.info(f'Client {sender.getpeername()} disconnected.')
                        for name in self.names:
                            if self.names[name] == sender:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(sender)

            for msg in self.messages:
                try:
                    self.process_message(msg, to_send_list)
                except (ConnectionAbortedError, ConnectionError, ConnectionRefusedError, ConnectionResetError):
                    u_name = msg[DESTINATION]
                    LOGGER.info(f'Connection with user "{u_name}" lost.')
                    self.clients.remove(self.names[u_name])
                    self.database.user_logout(u_name)
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
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config = configparser.ConfigParser()
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = parse_args(config[SETTINGS]['default_port'], config[SETTINGS]['listen_address'])

    database = ServerDB(
        os.path.join(
            config[SETTINGS]['database_path'],
            config[SETTINGS]['database_file'],
        )
    )

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global NEW_CONNECTION
        if NEW_CONNECTION:
            main_window.active_clients_table.setModel(gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with CONFLAG_LOCK:
                NEW_CONNECTION = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['database_path'])
        config_window.db_file.insert(config['SETTINGS']['database_file'])
        config_window.port.insert(config['SETTINGS']['default_port'])
        config_window.ip.insert(config['SETTINGS']['listen_address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['database_path'] = config_window.db_path.text()
        config['SETTINGS']['database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['listen_address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть числом от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main_server()
    os.system('pause')
