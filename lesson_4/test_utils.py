import json
import unittest

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from .common.test_variables import *
from lesson_3.common.variables import *
from lesson_3.common.utils import send_message, get_message


class TestUtils(unittest.TestCase):
    message = {
        ACTION: PRESENCE,
        TIME: TEST_TIME,
        USER: {
            ACCOUNT_NAME: TEST_USER,
        }
    }
    not_dict = 'not dict'

    server_socket = None
    client_socket = None

    def setUp(self):
        # сокет сервера
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_socket.bind((DEFAULT_IP_ADDRESS, DEFAULT_PORT))
        self.server_socket.listen(MAX_CONNECTIONS)

        # сокет клиента
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((DEFAULT_IP_ADDRESS, DEFAULT_PORT))

        self.client, self.client_address = self.server_socket.accept()

    def test_send_correct_message(self):
        send_message(self.client_socket, self.message)
        t_response = self.client.recv(MAX_PACKAGE_LENGTH)
        t_response = json.loads(t_response.decode(ENCODING))
        self.assertEqual(self.message, t_response)

    def test_send_wrong_message(self):
        self.assertRaises(TypeError, send_message, self.client_socket, self.not_dict)

    def test_get_message_dict(self):
        t_message = json.dumps(TEST_RESPONSE_OK)
        self.client.send(t_message.encode(ENCODING))
        self.assertIsInstance(get_message(self.client_socket), dict)

    def test_get_message_not_dict(self):
        t_message = json.dumps(self.not_dict)
        self.client.send(t_message.encode(ENCODING))
        self.assertRaises(ValueError, get_message, self.client_socket)

    def test_get_message_ok(self):
        t_message = json.dumps(TEST_RESPONSE_OK)
        self.client.send(t_message.encode(ENCODING))
        c_response = get_message(self.client_socket)
        self.assertEqual(TEST_RESPONSE_OK, c_response)

    def test_get_message_err(self):
        t_message = json.dumps(TEST_RESPONSE_ERR)
        self.client.send(t_message.encode(ENCODING))
        c_response = get_message(self.client_socket)
        self.assertEqual(TEST_RESPONSE_ERR, c_response)

    def tearDown(self):
        self.client.close()
        self.client_socket.close()
        self.server_socket.close()


if __name__ == '__main__':
    unittest.main()
