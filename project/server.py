import argparse
import socket
import sys
import select
import logging
import time

import project.logs.server_log_config

from project.common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, \
    RESPONSE_OK, RESPONSE_ERR, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from project.common.utils import get_message, send_message
from project.common.decorators import log

LOGGER = logging.getLogger('server')


@log
def process_client_message(message, messages_list, client, clients, names):
    LOGGER.debug(f'Processing message from {client.getpeername()}: {message}.')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_OK)
        else:
            response = RESPONSE_ERR
            response[ERROR] = 'This username already exists!'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return

    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message \
            and DESTINATION in message and SENDER in message and MESSAGE_TEXT in message:
        messages_list.append(message)
        return

    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        clients.remove(names[message[ACCOUNT_NAME]])
        names[message[ACCOUNT_NAME]].close()
        del names[message[ACCOUNT_NAME]]
        return

    response = RESPONSE_ERR
    response[ERROR] = 'Bad request. lol'
    send_message(client, response)
    return


@log
def process_message(message, names, listen_socks):
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        LOGGER.info(f'Message sent from "{message[SENDER]}" to "{message[DESTINATION]}"')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        text = f'User "{message[DESTINATION]}" not registered on server.'
        LOGGER.error(text)
        service_message = {
            ACTION: MESSAGE,
            SENDER: 'server',
            DESTINATION: message[SENDER],
            TIME: time.time(),
            MESSAGE_TEXT: text,
        }
        send_message(names[message[SENDER]], service_message)


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
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_address, listen_port))
    transport.settimeout(1)
    transport.listen(MAX_CONNECTIONS)

    clients = []
    messages = []
    names = dict()

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
                    process_client_message(message, messages, sender, clients, names)
                    LOGGER.info(f'Message received: {message}.')
                    del message
                except Exception:
                    LOGGER.info(f'Client {sender.getpeername()} disconnected.')
                    clients.remove(sender)

        for msg in messages:
            try:
                process_message(msg, names, to_send_list)
            except Exception:
                u_name = msg[DESTINATION]
                LOGGER.info(f'Connection with user "{u_name}" lost.')
                clients.remove(names[u_name])
                del names[u_name]
                del u_name
        messages.clear()


if __name__ == '__main__':
    main_server()
