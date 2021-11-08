import unittest
import common.variables as variables
from client import create_presence_message, process_answer

# Чтобы pycharm не выделял импорты красным и видел скрипты на уровень выше (как, например, здесь скрипт client),
# необходимо пометить папку подпроекта (в моём случае lesson_04) как ресурсную корневую. Их может быть несколько.
# Правая кнопка мыши на папке, пункт Mark Directory as, Sources Root.

CORRECT_TIME = 1.1
CORRECT_USER = 'Guest'
CUSTOM_PORT = 8888
CUSTOM_USER = 'Helen'

DEFAULT_CORRECT_MESSAGE = {
    variables.ACTION: variables.PRESENCE,
    variables.TIME: CORRECT_TIME,
    variables.PORT: variables.DEFAULT_PORT,
    variables.USER: {
        variables.ACCOUNT_NAME: CORRECT_USER
    }
}

CUSTOM_CORRECT_MESSAGE = {
    variables.ACTION: variables.PRESENCE,
    variables.TIME: CORRECT_TIME,
    variables.PORT: CUSTOM_PORT,
    variables.USER: {
        variables.ACCOUNT_NAME: CUSTOM_USER
    }
}

RESPONSE_200 = {variables.RESPONSE: 200}
RESPONSE_400 = {variables.RESPONSE: 400, variables.ERROR: 'Bad Request'}
RESPONSE_INCORRECT = {variables.ERROR: 'Bad Request'}
MESSAGE_200 = '200 : OK'
MESSAGE_400 = '400 : Bad Request'
EXPECTED_EXCEPTION = ValueError


class TestCaseClient(unittest.TestCase):

    def test_create_presence_message_default(self):
        """
        Тест создания корректного сообщения о присутствии клиента с параметрами по умолчанию
        """
        test_message = create_presence_message()
        test_message[variables.TIME] = CORRECT_TIME
        self.assertEqual(test_message, DEFAULT_CORRECT_MESSAGE)

    def test_create_presence_message_custom(self):
        """
        Тест создания корректного сообщения о присутствии клиента с пользовательскими параметрами
        """
        test_message = create_presence_message(CUSTOM_PORT, CUSTOM_USER)
        test_message[variables.TIME] = CORRECT_TIME
        self.assertEqual(test_message, CUSTOM_CORRECT_MESSAGE)

    def test_process_answer_200(self):
        """
        Тест преобразования ответа сервера при статусе ответа 200
        """
        self.assertEqual(process_answer(RESPONSE_200), MESSAGE_200)

    def test_process_answer_400(self):
        """
        Тест преобразования ответа сервера при статусе ответа 400
        """
        self.assertEqual(process_answer(RESPONSE_400), MESSAGE_400)

    def test_process_answer_incorrect(self):
        """
        Тест возбуждения исключения при некорректром ответе сервера
        """
        self.assertRaises(EXPECTED_EXCEPTION, process_answer, RESPONSE_INCORRECT)


if __name__ == '__main__':
    unittest.main()
