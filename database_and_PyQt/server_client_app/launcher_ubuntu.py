"""
Модуль-лаунчер для тестового запуска сервера и нескольких клиентов
"""


import os
import signal
import subprocess
import sys
from time import sleep
import argparse


PYTHON_PATH = sys.executable
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TEXT_FOR_INPUT = "Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: "


def get_params():
    """
    Функция получения параметров их командной строки
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-cn', type=int, default=2)
    params = parser.parse_args()
    return params.cn


def get_subprocess(file_with_args):
    """
    Функция создания подпроцесса
    """
    sleep(0.5)
    file_full_path = f"{PYTHON_PATH} {BASE_PATH}/{file_with_args}"
    args = ["gnome-terminal", "--disable-factory", "--", "bash", "-c", file_full_path]
    return subprocess.Popen(args, preexec_fn=os.setpgrp)


def main():
    """
    Основная функция модуля. Выводит консольный интерфейс для взаимодействия с пользователем,
    в зависитмости от полученных комманд запускает сервер и клиентов,
    останавливает их работу или выходит из программы
    """
    process = []
    count = get_params()
    while True:
        action = input(TEXT_FOR_INPUT)

        if action == "q":
            break
        elif action == "s":
            process.append(get_subprocess("server.py"))

            for i in range(count):
                process.append(get_subprocess(f"client.py"))

        elif action == "x":
            while process:
                victim = process.pop()
                os.killpg(victim.pid, signal.SIGINT)


if __name__ == "__main__":
    main()
