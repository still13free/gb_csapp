import unittest

from common.test_variables import *
from lesson_3.common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from lesson_3.client import create_presence, process_ans


class TestClient(unittest.TestCase):
    def setUp(self):
        pass

    def test_presence(self):
        # Переменные, начинающие с префикса t_ — тестовые данные
        t_presence = create_presence(TEST_USER)
        t_presence[TIME] = TEST_TIME

        # Переменные, начинающие с префикса с_ — контрольные данные
        c_presence = {
            ACTION: PRESENCE,
            TIME: TEST_TIME,
            USER: {
                ACCOUNT_NAME: TEST_USER
            }
        }

        self.assertEqual(t_presence, c_presence)

    def test_answer_200(self):
        c_answer = '200: OK'
        self.assertEqual(process_ans(TEST_RESPONSE_OK), c_answer)

    def test_answer_400(self):
        c_answer = '400: Bad Request'
        self.assertEqual(process_ans(TEST_RESPONSE_ERR), c_answer)

    def test_no_response(self):
        t_message = {'nothing': None}
        self.assertRaises(ValueError, process_ans, t_message)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
