# Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе.

def no_bytes_format(*args):
    result = []
    for item in args:
        try:
            bytes(item, encoding='ASCII')
        except UnicodeEncodeError:
            result.append(item)
    return result


if __name__ == '__main__':

    print(*no_bytes_format('attribute', 'класс', 'функция', 'type'), sep='\n')
