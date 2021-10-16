# Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет», «декоратор».
# Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести его содержимое

import chardet


def unicode_file_open(filepath):
    with open(filepath, 'br') as file:
        encoding = None
        for line in file:
            if not encoding:
                encoding = chardet.detect(line).get('encoding')
            print(line.decode(encoding).encode('UTF-8').decode('UTF-8'), end='')


with open('test_file.txt', 'w') as test_file:
    print('сетевое программирование\nсокет\nдекоратор', file=test_file)
    print('Кодировка по умолчанию:', test_file.encoding)

print('\nРезультат открытия файла в кодировке UTF-8:')
unicode_file_open('test_file.txt')
