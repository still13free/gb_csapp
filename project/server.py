import argparse
import json
import socket
import sys
import logging
import project.logs.server_log_config

from project.common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, \
    RESPONSE, ERROR
from project.common.utils import get_message, send_message
from project.common.errors import IncorrectDataReceivedError
from project.common.decorators import log

LOGGER = logging.getLogger('server')


@log
def process_client_message(message):
    LOGGER.debug(f'Processing message from client: {message}.')
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad Request',
    }


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    return parser


def main_server():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        LOGGER.critical(f'Attempting to launch server with wrong port number: {listen_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Server terminates.')
        sys.exit(1)
    LOGGER.info(f'Launched server, port for connections: {listen_port}. '
                f'Listen address - {listen_address} (if not specified - any).')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_address, listen_port))
    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        LOGGER.info(f'Connection established with {client_address}.')
        try:
            message_from_client = get_message(client)
            LOGGER.info(f'Message received: {message_from_client}.')

            response = process_client_message(message_from_client)
            LOGGER.info(f'Response generated: {response}.')
            send_message(client, response)

        except json.JSONDecodeError:
            LOGGER.error('Failed to decode json-string message')

        except IncorrectDataReceivedError:
            LOGGER.error('Received incorrect data')

        finally:
            LOGGER.info(f'Connection closed with {client_address}')
            client.close()


if __name__ == '__main__':
    main_server()
