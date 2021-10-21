"""
Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата.
Для этого:

a. Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом, отсутствующим
в кодировке ASCII (например, €);

b. Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. При этом обеспечить стилизацию файла
с помощью параметра default_flow_style, а также установить возможность работы с юникодом: allow_unicode = True;

c. Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""

import yaml
from random import randint
from pprint import pprint

DATA_WRITE = {
    'first': [f'value_{item:02d}' for item in range(1, 11)],
    'second': randint(1, 100),
    'third': {
        key: randint(1, 100) for key in
        (f'{item}-{chr(item)}' for item in range(1040, 1051))
    },
}

FILENAME = 'yaml_test.yaml'

with open(FILENAME, 'w', encoding='UTF-8') as file:
    yaml.dump(DATA_WRITE, file, default_flow_style=False, allow_unicode=True)

with open(FILENAME, encoding='UTF-8') as file:
    DATA_READ = yaml.load(file, yaml.Loader)

print('Словарь для записи в yaml-файл:')
pprint(DATA_WRITE)

print('\nСловарь, выгруженный из yaml-файла:')
pprint(DATA_READ)

print('\nСовпадают ли словари:', DATA_WRITE == DATA_READ)
