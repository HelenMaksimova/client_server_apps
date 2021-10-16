# Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность
# кодов (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.

def bytes_info(*args):
    for b_string in args:
        print('*************************************')
        print(b_string, type(b_string), len(b_string))
        print('*************************************\n')


if __name__ == '__main__':

    BYTES_1 = b'class'
    BYTES_2 = b'function'
    BYTES_3 = b'method'

    bytes_info(BYTES_1, BYTES_2, BYTES_3)
