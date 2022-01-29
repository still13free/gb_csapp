import argparse
import json
import socket
import sys
import select
import time
import logging
import project.logs.server_log_config

from project.common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, \
    RESPONSE_OK, RESPONSE_ERR, MESSAGE, MESSAGE_TEXT, SENDER
from project.common.utils import get_message, send_message
from project.common.decorators import log

LOGGER = logging.getLogger('server')


@log
def process_client_message(message, messages_list, client):
    LOGGER.debug(f'Processing message from client: {message}.')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        send_message(client, RESPONSE_OK)
        return

    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and MESSAGE_TEXT in message:
        messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
        return

    send_message(client, RESPONSE_ERR)
    return


@log
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        LOGGER.critical(f'Attempting to launch server with wrong port number: {listen_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Server terminates.')
        sys.exit(1)
    return listen_address, listen_port


def main_server():
    listen_address, listen_port = parse_args()

    LOGGER.info(f'Launched server, port for connections: {listen_port}. '
                f'Listen address - {listen_address} (if not specified - any).')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)
    transport.listen(MAX_CONNECTIONS)

    clients = []
    messages = []

    while True:
        try:
            client, client_address = transport.accept()
        except OSError:
            pass
        else:
            LOGGER.info(f'Connection established with {client_address}.')
            clients.append(client)

        to_recv_list = []
        to_send_list = []
        err_list = []

        try:
            if clients:
                to_recv_list, to_send_list, err_list = select.select(clients, clients, [], 0)
        except OSError:
            pass

        if to_recv_list:
            for sender in to_recv_list:
                try:
                    message = get_message(sender)
                    process_client_message(message, messages, sender)
                    LOGGER.info(f'Message received: {message}.')
                except:
                    LOGGER.info(f'Client {sender.getpeername()} disconnected.')
                    clients.remove(sender)

        if messages and to_send_list:
            message = {
                ACTION: MESSAGE,
                SENDER: messages[0][0],
                TIME: time.time(),
                MESSAGE_TEXT: messages[0][1],
            }
            del messages[0]
            for recipient in to_send_list:
                try:
                    send_message(recipient, message)
                except:
                    LOGGER.info(f'Client {recipient.getpeername()} disconnected.')
                    recipient.close()
                    clients.remove(recipient)


if __name__ == '__main__':
    main_server()
