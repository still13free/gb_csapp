import argparse
import socket
import sys
import select
import time
import logging
import project.logs.server_log_config

from project.common.variables import *
from project.common.utils import get_message, send_message
from project.common.decorators import log
from project.common.descriptors import Port
from project.common.metaclasses import ServerMaker

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


class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port):
        self.addr = listen_address
        self.port = listen_port
        self.clients = []
        self.messages = []
        self.names = dict()

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
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_OK)
            else:
                response = RESPONSE_ERR
                response[ERROR] = 'This username already exists!'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message \
                and DESTINATION in message and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return

        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            u_name = message[ACCOUNT_NAME]
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

    def main_loop(self):
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


def main_server():
    listen_address, listen_port = parse_args()

    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main_server()
