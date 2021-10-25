"""
Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах. Написать скрипт,
автоматизирующий его заполнение данными. Для этого:

a. Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item), количество (quantity),
цена (price), покупатель (buyer), дата (date). Функция должна предусматривать запись данных в виде словаря
в файл orders.json. При записи данных указать величину отступа в 4 пробельных символа;

b. Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра.
"""

import json
from typing import List


# Первый вариант (с именованными параметрами):
def write_order_to_json(filepath: str, **kwargs):
    """
    Функция для записи данных заказа в json-файл
    :param filepath: путь к файлу
    :param kwargs: именованные параметры, которые в виде словаря добавляются в файл.
    :return: None
    """
    with open(filepath, encoding='UTF-8') as json_file:
        data = json.load(json_file)

    data['orders'].append(kwargs)

    with open(filepath, 'w', encoding='UTF-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


# Второй вариант вариант (с позиционными параметрами):
def write_order_to_json_v2(filepath: str, keys: List[str], *values):
    """
    Функция для записи данных заказа в json-файл
    :param filepath: путь к файлу
    :param keys: названия полей (ключи словаря)
    :param values: значения полей (значения словаря)
    :return: None
    """

    with open(filepath, encoding='UTF-8') as json_file:
        data = json.load(json_file)

    data_dict = {element[0]: element[1] for element in zip(keys, values)}

    data['orders'].append(data_dict)

    with open(filepath, 'w', encoding='UTF-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':

    FILEPATH = 'orders.json'

    # Запись данных в файл с ипользованием первой функции:
    DATA_DICT = [
        {'item': 'Юбка',
         'quantity': 1,
         'price': 1500.0,
         'buyer': 'Татьяна Татьянина',
         'date': '13-04-2021'},
    ]

    for item in DATA_DICT:
        write_order_to_json(FILEPATH, **item)

    # Запись данных в файл с ипользованием второй функции:
    FIELDS = ['item', 'quantity', 'price', 'buyer', 'date']
    DATA_LIST = [
        ('Брюки', 2, 5574.16, 'Кирилл Кириллов', '09-09-2021'),
        ('Юла', 3, 600.12, 'Константин Константинов', '31-12-2020'),
    ]

    for item in DATA_LIST:
        write_order_to_json_v2(FILEPATH, FIELDS, *item)
