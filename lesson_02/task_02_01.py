"""
Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных
из файлов info_1.txt, info_2.txt, info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого:

a. Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и
считывание данных. В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь
значения параметров «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». З
начения каждого параметра поместить в соответствующий список. Должно получиться четыре списка —
например, os_prod_list, os_name_list, os_code_list, os_type_list.
В этой же функции создать главный список для хранения данных отчета — например, main_data —
и поместить в него названия столбцов отчета в виде списка:
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла);

b. Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(),
а также сохранение подготовленных данных в соответствующий CSV-файл;

c. Проверить работу программы через вызов функции write_to_csv().
"""

import csv
import chardet
import re
from collections import defaultdict
from typing import List


def get_encoding(filename: str) -> str:
    """
    Функция для определения кодировки файла
    :param filename: путь к файлу в виде строки
    :return: кодировка в виде строки
    """
    with open(filename, 'br') as file:
        detector = chardet.UniversalDetector()
        for line in file:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result.get('encoding')


def get_data(headers: List[str], files: List[str]) -> List[list]:
    """
    Функция для поиска и преобразования данных из нескольких файлов
    для последующей записи в единый файл в формате csv

    Переменные функции:
    patterns - список шаблонов (регулярных выражений) для посика данных в файлах;
    data_dict - словарь, содержащий результаты парсинга данных. Ключи - заголовки столбцов,
    значения - списки найденных данных (в формате строк);
    gen_for_zip - генератор, содержащий списки данных, упорядоченные по значениям заголовков,
    использующийся для дальнейшего поэлементного объединения списков и записи их в итоговую структуру данных;
    result_data_lst - итоговая структура данных, возвращаемая функцией.

    :param headers: список заголовков столбцов
    :param files: список файлов
    :return: список списков, в котором первый элемент - строка заголовков,
    последующие элементы - строки данных
    """
    patterns = [re.compile(param) for param in headers]
    data_dict = defaultdict(list)
    for file in files:
        encoding = get_encoding(file)
        with open(file, encoding=encoding) as parsed_file:
            for line in parsed_file:
                for pattern in patterns:
                    if re.match(pattern, line):
                        item = line.strip().split(':')
                        data_dict[item[0]].append(item[1].strip())
    gen_for_zip = (data_dict[name] for name in headers)
    result_data_lst = [headers]
    result_data_lst.extend([list(item) for item in zip(*gen_for_zip)])
    return result_data_lst


def write_to_csv(filename: str, headers: List[str], files: List[str]):
    """
    Функция для преобразования данных из нескольких файлов и записи в единый файл в формате csv
    :param filename: путь к файлу в виде строки
    :param headers: список заголовков столбцов
    :param files: список файлов
    :return: None
    """
    data = get_data(headers, files)
    with open(filename, 'w', encoding='UTF-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(data)


if __name__ == '__main__':

    FILES = ['info_1.txt', 'info_2.txt', 'info_3.txt']
    HEADERS = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']

    write_to_csv('data.csv', HEADERS, FILES)
