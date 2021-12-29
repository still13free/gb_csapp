"""
1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и
    проверить тип и содержание соответствующих переменных.
    Затем с помощью онлайн-конвертера преобразовать строковые представление в формат Unicode и
    также проверить тип и содержимое переменных.
"""
from lesson_1.variables import DELIMITER_25


def print_value_and_type(var_list: list):
    print(DELIMITER_25)
    print('==== variable - type ====')
    print(DELIMITER_25)
    for var in var_list:
        print(f'{var} - {type(var)}')
    print(DELIMITER_25, end='\n\n')


WORD_1 = 'разработка'
WORD_2 = 'сокет'
WORD_3 = 'декоратор'
WORDS = [WORD_1, WORD_2, WORD_3]

WORD_1_UNICODE = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
WORD_2_UNICODE = '\u0441\u043e\u043a\u0435\u0442'
WORD_3_UNICODE = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
UNICODE_LIST = [WORD_1_UNICODE, WORD_2_UNICODE, WORD_3_UNICODE]

print_value_and_type(WORDS)
print_value_and_type(UNICODE_LIST)
