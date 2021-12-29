"""
4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в байтовое
    и выполнить обратное преобразование (используя методы encode и decode)
"""
from lesson_1.variables import DELIMITER_100


def print_encode_list(str_list: list, decode=False):
    result = []
    print(DELIMITER_100)
    print('=== Converting to byte string:')
    for word in str_list:
        bytes_word = word.encode('utf-8')
        print(bytes_word)
        result.append(bytes_word)
    print(DELIMITER_100)
    if decode:
        print_decode_list(result)
    else:
        return result


def print_decode_list(bytes_list: list, encode=False):
    result = []
    print(DELIMITER_100)
    print('=== Converting from bytes to string:')
    for bytes_word in bytes_list:
        word = bytes_word.decode('utf-8')
        print(word)
        result.append(word)
    print(DELIMITER_100)
    if encode:
        print_encode_list(result)
    else:
        return result


WORD_1 = 'разработка'
WORD_2 = 'администрирование'
WORD_3 = 'protocol'
WORD_4 = 'standard'

WORDS = [WORD_1, WORD_2, WORD_3, WORD_4]

# print_encode_list(WORDS, decode=True)

bytes_words = print_encode_list(WORDS)
words = print_decode_list(bytes_words)
