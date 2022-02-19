import argparse
import json
import socket
import sys
import time
import threading
import logging
import logs.client_log_config

from common.variables import *
from common.utils import send_message, get_message
from common.errors import RequiredFieldMissingError, IncorrectDataReceivedError, ServerError
from common.decorators import log
from common.metaclasses import ClientMaker

LOGGER = logging.getLogger('client')


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_message(self):
        to_user = input('Enter message recipient: ')
        message = input('Enter message itself: ')
        message_to_send = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        LOGGER.debug(f'Message created: {message_to_send}')

        try:
            send_message(self.sock, message_to_send)
            LOGGER.info(f'Message sent to "{to_user}"')
        except Exception as e:
            print(e)
            LOGGER.critical(f'Server connection lost.')
            exit(1)

    def create_exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
        }

    def run(self):
        self.print_help()
        while True:
            command = input('Enter command: ')
            if command == '!m' or command == 'message':
                self.create_message()
            elif command == '!h' or command == 'help':
                self.print_help()
            elif command == '!x' or command == 'exit':
                try:
                    send_message(self.sock, self.create_exit_message())
                except Exception as e:
                    LOGGER.error(e)
                LOGGER.info('Shutdown by user command.')
                print('Shutdown. Thank you for using our service!')
                time.sleep(1)
                break
            else:
                print('Unknown command. Enter "!h" OR "help" without quotes to get supported commands.')

    @staticmethod
    def print_help():
        print('Supported commands:'
              '\n\t - !m OR message - sending message'
              '\n\t - !h OR help - print this help'
              '\n\t - !x OR exit - close program')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                        and message[DESTINATION] == self.account_name and MESSAGE_TEXT in message:
                    text = f'Message received from user "{message[SENDER]}": {message[MESSAGE_TEXT]}'
                    LOGGER.info(text)
                    print('\n' + text)
                    del text
                else:
                    LOGGER.error(f'Received incorrect message from server: {message}.')
            except IncorrectDataReceivedError:
                LOGGER.error(f'Failed to decode received message.')
            except (OSError, ConnectionError, ConnectionResetError, ConnectionAbortedError, json.JSONDecodeError):
                LOGGER.critical(f'Server connection lost.')
                break


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
        receiver = ClientReader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        sender = ClientSender(client_name, transport)
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
