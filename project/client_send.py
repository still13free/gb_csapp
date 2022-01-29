import argparse
import json
import time
import socket
import sys
import logging
import project.logs.client_log_config

from project.common.variables import ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, RESPONSE, ERROR, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS, SENDER, MESSAGE, MESSAGE_TEXT, MODE_LISTEN, MODE_SEND
from project.common.utils import send_message, get_message
from project.common.errors import RequiredFieldMissingError, IncorrectDataReceivedError, ServerError
from project.common.decorators import log

LOGGER = logging.getLogger('client')


@log
def process_message(message):
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message:
        text = f'Message received from user {message[SENDER]}: {message[MESSAGE_TEXT]}.'
        print(text)
        LOGGER.info(text)
    else:
        LOGGER.error(f'Received incorrect message from server: {message}.')


@log
def create_message(sock, account_name='Guest'):
    exit_command = '!!!'
    message = input(f'Enter message or command "{exit_command}" to exit: ')
    if message == exit_command:
        sock.close()
        LOGGER.info('Shutdown by user command.')
        print('Shutdown. Thank you for using service!')
        sys.exit(0)
    message_to_send = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message,
    }
    LOGGER.debug(f'Message created: {message_to_send}')
    return message_to_send


@log
def create_presence(account_name='Guest'):
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
    parser.add_argument('-m', '--mode', default=MODE_SEND, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Attempting to launch client with wrong port number: {server_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Client terminates.')
        sys.exit(1)

    modes = (MODE_LISTEN, MODE_SEND)
    if client_mode not in (MODE_LISTEN, MODE_SEND):
        LOGGER.critical(f'Incorrect mode "{client_mode}", must be {modes}')
        sys.exit(1)

    return server_address, server_port, client_mode


def main_client():
    server_address, server_port, client_mode = parse_args()
    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, port - {server_port}, mode - {client_mode}.')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))

        send_message(transport, create_presence())
        answer = process_ans(get_message(transport))
        LOGGER.info(f'Connection established. Response received from server: {answer}.')
        print(f'Connection established with server.')

    except json.JSONDecodeError:
        LOGGER.error('Failed to decode json-string message.')
        sys.exit(1)

    except ServerError as err:
        LOGGER.error(f'Server returned error while establishing connection: {err.text}.')
        sys.exit(1)

    except ConnectionRefusedError:
        LOGGER.critical(f'Failed to connect to server {server_address}:{server_port}. '
                        f'Server refused connection request.')
        sys.exit(1)

    except RequiredFieldMissingError as err:
        LOGGER.error(f'Required field is missing in server response: {err.missing_field}.')
        sys.exit(1)

    else:
        print(f'Mode: "{client_mode}"')

    conn_err_msg = f'Connection with server {server_address}:{server_port} lost.'
    while True:
        if client_mode == MODE_SEND:
            try:
                send_message(transport, create_message(transport))
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                LOGGER.error(conn_err_msg)
                sys.exit(1)

        if client_mode == MODE_LISTEN:
            try:
                process_message(get_message(transport))
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                LOGGER.error(conn_err_msg)
                sys.exit(1)


if __name__ == '__main__':
    main_client()
