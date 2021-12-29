"""
2. Каждое из слов «class», «function», «method» записать в байтовом типе. Сделать это необходимо в автоматическом,
    а не ручном режиме с помощью добавления литеры b к текстовому значению, (т.е. ни в коем случае не используя методы
    encode и decode) и определить тип, содержимое и длину соответствующих переменных.
"""
from lesson_1.variables import DELIMITER_50


def get_byte_str(str_list: list):
    print(DELIMITER_50)
    print(f'===== type ======== variable ======== length =====')
    print(DELIMITER_50)
    for string in str_list:
        string = eval(f"b'{string}'")
        print(f'{type(string)}\t\t{string}\t\t{len(string)}')
    print(DELIMITER_50)


WORD_1 = 'class'
WORD_2 = 'function'
WORD_3 = 'method'
WORDS = [WORD_1, WORD_2, WORD_3]

get_byte_str(WORDS)
