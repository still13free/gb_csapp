import json
import time
import socket
import sys

from lesson_3.variables import ACTION, TIME, USER, ACCOUNT_NAME, PRESENCE, RESPONSE, ERROR, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from lesson_3.utils import send_message, get_message


def create_presence(account_name='Guest'):
    out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return out


def process_ans(message):
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        return f'400: {message[ERROR]}'
    raise ValueError


def main():
    try:
        server_address = sys.argv[1]
        server_port = sys.argv[2]
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        print('Port number must be integer in range [1024, 65535]')
        sys.exit(1)

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.connect((server_address, server_port))
    message_to_server = create_presence()
    send_message(transport, message_to_server)
    try:
        answer = process_ans(get_message(transport))
        print(answer)
    except (ValueError, json.JSONDecodeError):
        print('Failed to decode message')
    finally:
        transport.close()


if __name__ == '__main__':
    main()
