# Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления
# в байтовое и выполнить обратное преобразование (используя методы encode и decode).

from task_01_01 import string_info


def encode_decode(*args):
    for string in args:
        print(string)
        b_string = string.encode('utf-8')
        string_info(b_string)
        string = b_string.decode('utf-8')
        string_info(string)


if __name__ == '__main__':

    encode_decode('разработка', 'администрирование', 'protocol', 'standard')
