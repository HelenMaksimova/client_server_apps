import json
import unittest
from common.utils import send_message, get_message
import common.variables as variables
import os


class TestSocket:
    """
    Класс тестового сокета на основе файла. Отправка данных - запись байт в файл.
    Получение данных - считывание байт из файла.
    """

    def __init__(self, socket_name: str):
        """Инициализация объекта. Создаётся файл с именем, переданным в параметрах"""
        self.socket_name = socket_name
        with open(socket_name, 'w', encoding='utf-8'):
            pass

    def send(self, data: bytes):
        """
        Записывает в файл данные в байтах
        :param data: данные в байтах
        :return: None
        """
        with open(self.socket_name, 'bw') as socket:
            socket.write(data)

    def recv(self, max_len=1024):
        """
        Считывает данные из файла в байтах
        :param max_len: максимальная длина считываемых данных (байт)
        :return: данные в байтах
        """
        with open(self.socket_name, 'br') as socket:
            data = socket.read(max_len)
        return data


class TestCaseUtils(unittest.TestCase):

    SOCKET_NAME = 'test_socket'

    TEST_MESSAGE = {
        variables.ACTION: variables.PRESENCE,
        variables.TIME: 1.1,
        variables.PORT: variables.DEFAULT_PORT,
        variables.USER: {
            variables.ACCOUNT_NAME: 'Guest'
        }
    }

    RESPONSE_200 = {variables.RESPONSE: 200}
    RESPONSE_400 = {variables.RESPONSE: 400, variables.ERROR: 'Bad Request'}

    def setUp(self):
        """
        При запуске тестов создаётся тестовый сокет
        """
        self.socket = TestSocket(self.SOCKET_NAME)

    def tearDown(self):
        """
        После окончания тестирования тестовый сокет удаляется
        """
        os.remove(self.SOCKET_NAME)

    def right_encoding(self, message):
        """
        Метод возвращает корректно кодированное в байты сообщение
        :param message: сообщение
        :return: bytes
        """
        return message.encode(variables.ENCODING)

    def test_send_message(self):
        """
        Тест корректной кодировки и записи сообщения в сокет
        """
        send_message(self.socket, self.TEST_MESSAGE)
        string_message = json.dumps(self.TEST_MESSAGE)
        encoded_message = self.right_encoding(string_message)
        self.assertEqual(encoded_message, self.socket.recv())

    def test_send_message_incorrect(self):
        """
        Тест возбуждения исключения в случае передачи в функцию send_message некорректного параметра
        """
        string_message = json.dumps(self.TEST_MESSAGE)
        self.assertRaises(TypeError, send_message, string_message)

    def test_get_message_response_200(self):
        """
        Тест получения корректного словаря с ответом сервера 200 из сокета
        """
        send_message(self.socket, self.RESPONSE_200)
        message = get_message(self.socket)
        self.assertEqual(message, self.RESPONSE_200)

    def test_get_message_response_400(self):
        """
        Тест получения корректного словаря с ответом сервера 400 из сокета
        """
        send_message(self.socket, self.RESPONSE_400)
        message = get_message(self.socket)
        self.assertEqual(message, self.RESPONSE_400)
