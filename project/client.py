import argparse
import json
import time
import socket
import sys
import logging
import project.logs.client_log_config

from project.common.variables import ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, RESPONSE, ERROR, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS
from project.common.utils import send_message, get_message
from project.common.errors import RequiredFieldMissingError, IncorrectDataReceivedError
from project.common.decorators import log

LOGGER = logging.getLogger('client')


@log
def create_presence(account_name='Guest'):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    LOGGER.debug(f'{PRESENCE}-message generated for user "{account_name}".')
    return out


@log
def process_ans(message):
    LOGGER.debug(f'Processing message from server: {message}.')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        return f'400: {message[ERROR]}'
    raise RequiredFieldMissingError(RESPONSE)


def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    return parser


def main_client():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port

    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Attempting to launch client with wrong port number: {server_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Client terminates.')
        sys.exit(1)
    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, port - {server_port}.')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        message_to_server = create_presence()
        send_message(transport, message_to_server)

        answer = process_ans(get_message(transport))
        LOGGER.info(f'Response received from server: {answer}.')
        print(answer)

    except json.JSONDecodeError:
        LOGGER.error('Failed to decode json-string message.')

    except ConnectionRefusedError:
        LOGGER.critical(f'Failed to connect to server {server_address}:{server_port}. '
                        f'Server refused connection request.')

    except IncorrectDataReceivedError:
        LOGGER.error('Received incorrect data')

    except RequiredFieldMissingError as err:
        LOGGER.error(f'Required field is missing in server response: {err.missing_field}.')

    finally:
        transport.close()


if __name__ == '__main__':
    main_client()
