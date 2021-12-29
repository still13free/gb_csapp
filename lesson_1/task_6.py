"""
6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет», «декоратор».
    Проверить кодировку созданного файла (исходить из того, что вам априори неизвестна кодировка этого файла!).
    Затем открыть этот файл и вывести его содержимое на печать.

    ВАЖНО: файл должен быть открыт без ошибок вне зависимости от того, в какой кодировке он был создан!
"""
from chardet import detect


def create_test_file(content: list, file_name='test_file.txt', encoding='utf-8'):
    file = open(file_name, 'w', encoding=encoding)
    for line in content:
        file.write(f'{line}\n')
    file.close()
    return file_name


def detect_encoding(file_name: str):
    with open(file_name, 'rb') as file:
        content = file.read()
    encoding = detect(content)['encoding']
    print('encoding: ', encoding)
    return encoding


def print_file_content(file_name: str, encoding: str):
    with open(file_name, 'r', encoding=encoding) as file:
        content = file.read()
    print(content)


CONTENT_LINES = ['сетевое программирование', 'сокет', 'декоратор']

f_name = create_test_file(CONTENT_LINES, encoding='IBM866')
# f_name = create_test_file(CONTENT_LINES)
f_encoding = detect_encoding(f_name)
print_file_content(f_name, f_encoding)
