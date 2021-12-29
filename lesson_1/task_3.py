"""
3. Определить, какие из слов, поданных на вход программы, невозможно записать в байтовом типе. Для проверки
    правильности работы кода используйте значения: «attribute», «класс», «функция», «type»
"""


def check_convert_to_byte(str_list: list):
    for string in str_list:
        if string.isascii():
            print(f'OK: word "{string}" can be converted to byte string')
        else:
            print(f'Fail: word "{string}" cannot be written as a byte string')


WORD_1 = 'attribute'
WORD_2 = 'класс'
WORD_3 = 'функция'
WORD_4 = 'type'

WORDS = [WORD_1, WORD_2, WORD_3, WORD_4]

check_convert_to_byte(WORDS)
