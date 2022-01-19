import unittest

from common.test_variables import *
from lesson_3.common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from lesson_3.server import process_client_message


class TestServer(unittest.TestCase):
    account_name = 'Guest'

    def setUp(self):
        pass

    def test_process_ok(self):
        t_message = {ACTION: PRESENCE, TIME: TEST_TIME, USER: {ACCOUNT_NAME: self.account_name}}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_OK)

    def test_no_action(self):
        t_message = {TIME: TEST_TIME, USER: {ACCOUNT_NAME: self.account_name}}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_ERR)

    def test_unknown_action(self):
        t_message = {ACTION: 'unknown', TIME: TEST_TIME, USER: {ACCOUNT_NAME: self.account_name}}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_ERR)

    def test_no_time(self):
        t_message = {ACTION: PRESENCE, USER: {ACCOUNT_NAME: self.account_name}}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_ERR)

    def test_no_user(self):
        t_message = {ACTION: PRESENCE, TIME: TEST_TIME}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_ERR)

    def test_unknown_user(self):
        t_message = {ACTION: PRESENCE, TIME: TEST_TIME, USER: {ACCOUNT_NAME: 'unknown_user'}}
        self.assertEqual(process_client_message(t_message), TEST_RESPONSE_ERR)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
