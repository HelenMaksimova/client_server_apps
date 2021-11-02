import unittest
import common.variables as variables
from server import process_client_message

CORRECT_ACTION = variables.PRESENCE
CORRECT_USER = 'Guest'
INCORRECT_ACTION = 'some_action'
INCORRECT_USER = 'some_user'
TIME = 1.1
PORT = variables.DEFAULT_PORT

ERROR_RESPONSE = {
    variables.RESPONSE: 400,
    variables.ERROR: 'Bad Request'
}

OK_RESPONSE = {variables.RESPONSE: 200}


class TestCaseServer(unittest.TestCase):

    def test_process_client_message_correct(self):
        """
        Тест формирования ответа на корректное presence сообщение клиента
        """
        client_message = {
            variables.ACTION: CORRECT_ACTION,
            variables.TIME: TIME,
            variables.PORT: PORT,
            variables.USER: {
                variables.ACCOUNT_NAME: CORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), OK_RESPONSE)

    def test_process_client_message_no_action(self):
        """
        Тест формирования ответа на presence сообщение клиента без параметра action
        """
        client_message = {
            variables.TIME: TIME,
            variables.PORT: PORT,
            variables.USER: {
                variables.ACCOUNT_NAME: CORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)

    def test_process_client_message_no_time(self):
        """
        Тест формирования ответа на presence сообщение клиента без параметра time
        """
        client_message = {
            variables.ACTION: CORRECT_ACTION,
            variables.PORT: PORT,
            variables.USER: {
                variables.ACCOUNT_NAME: CORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)

    def test_process_client_message_no_user(self):
        """
        Тест формирования ответа на presence сообщение клиента без параметра user
        """
        client_message = {
            variables.ACTION: CORRECT_ACTION,
            variables.TIME: TIME,
            variables.PORT: PORT
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)

    def test_process_client_message_no_port(self):
        """
        Тест формирования ответа на presence сообщение клиента без параметра port
        """
        client_message = {
            variables.ACTION: CORRECT_ACTION,
            variables.TIME: TIME,
            variables.USER: {
                variables.ACCOUNT_NAME: CORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)

    def test_process_client_message_wrong_action(self):
        """
        Тест формирования ответа на presence сообщение клиента с неверным параметром action
        """
        client_message = {
            variables.ACTION: INCORRECT_ACTION,
            variables.TIME: TIME,
            variables.PORT: PORT,
            variables.USER: {
                variables.ACCOUNT_NAME: CORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)

    def test_process_client_message_wrong_user(self):
        """
        Тест формирования ответа на presence сообщение клиента с неизвестным пользователем
        """
        client_message = {
            variables.ACTION: CORRECT_ACTION,
            variables.TIME: TIME,
            variables.PORT: PORT,
            variables.USER: {
                variables.ACCOUNT_NAME: INCORRECT_USER
            }
        }
        self.assertEqual(process_client_message(client_message), ERROR_RESPONSE)
