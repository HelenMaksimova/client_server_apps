# Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый тип
# на кириллице.

import subprocess
import chardet


def resource_ping(address, count):
    args = ['ping', address, '-c', str(count)]
    ping_process = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in ping_process.stdout:
        encoding = chardet.detect(line).get('encoding')
        line = line.decode(encoding).encode('utf-8').decode('utf-8')
        print(line, end='')


resource_ping('yandex.ru', 4)

resource_ping('youtube.com', 4)
