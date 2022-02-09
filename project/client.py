import argparse
import json
import time
import socket
import sys
import threading
import logging
import project.logs.client_log_config

from project.common.variables import ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, RESPONSE, ERROR, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS, SENDER, MESSAGE, MESSAGE_TEXT, DESTINATION, EXIT
from project.common.utils import send_message, get_message
from project.common.errors import RequiredFieldMissingError, IncorrectDataReceivedError, ServerError
from project.common.decorators import log

LOGGER = logging.getLogger('client')


@log
def process_server_message(sock, my_username):
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in message \
                    and DESTINATION in message and message[DESTINATION] == my_username and MESSAGE_TEXT in message:
                text = f'Message received from user {message[SENDER]}: {message[MESSAGE_TEXT]}.'
                print('\n' + text)
                LOGGER.info(text)
            else:
                LOGGER.error(f'Received incorrect message from server: {message}.')
        except IncorrectDataReceivedError:
            LOGGER.error(f'Failed to decode received message.')
        except (OSError, ConnectionError, ConnectionResetError, ConnectionAbortedError, json.JSONDecodeError):
            LOGGER.critical(f'Server connection lost.')
            break


@log
def create_exit_message(account_name):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
    }


@log
def create_message(sock, account_name='Guest'):
    to_user = input('Enter message recipient: ')
    message = input('Enter message itself: ')
    message_to_send = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message,
    }
    LOGGER.debug(f'Message created: {message_to_send}')

    try:
        send_message(sock, message_to_send)
        LOGGER.info(f'Message sent to "{to_user}"')
    except Exception as e:
        print(e)
        LOGGER.critical(f'Server connection lost.')
        sys.exit(1)


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
def user_interactive(sock, username):
    print_help()
    while True:
        command = input('Enter command: ')
        if command == '!m' or command == 'message':
            create_message(sock, username)
        elif command == '!h' or command == 'help':
            print_help()
        elif command == '!x' or command == 'exit':
            send_message(sock, create_exit_message(username))
            LOGGER.info('Shutdown by user command.')
            print('Shutdown. Thank you for using our service!')
            time.sleep(1)
            break
        else:
            print('Unknown command. Enter "!h" OR "help" without quotes to get supported commands.')


@log
def print_help():
    print('Supported commands:'
          '\n\t - !m OR message - sending message'
          '\n\t - !h OR help - print this help'
          '\n\t - !x OR exit - close program')


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
        transport.connect((server_address, server_port))

        send_message(transport, create_presence(client_name))
        answer = process_ans(get_message(transport))
        LOGGER.info(f'Connection established. Response received from server: {answer}.')
        print(f'Connection established with server.')

    except json.JSONDecodeError:
        LOGGER.error('Failed to decode json-string message.')
        sys.exit(1)

    except ServerError as err:
        LOGGER.error(f'Server returned error while establishing connection: {err.text}.')
        sys.exit(1)

    except RequiredFieldMissingError as err:
        LOGGER.error(f'Required field is missing in server response: {err.missing_field}.')
        sys.exit(1)

    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(f'Failed to connect to server {server_address}:{server_port}. '
                        f'Server refused connection request.')
        sys.exit(1)

    else:
        receiver = threading.Thread(target=process_server_message, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()

        LOGGER.debug('Processes running!')

    while True:
        time.sleep(1)
        if receiver.is_alive() and user_interface.is_alive():
            continue
        break


if __name__ == '__main__':
    main_client()
