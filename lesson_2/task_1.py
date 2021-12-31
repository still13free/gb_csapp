"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку определенных данных из файлов
    info_1.txt, info_2.txt, info_3.txt и формирующий новый «отчетный» файл в формате CSV. Для этого:

    Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и
    считывание данных. В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения
    параметров «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
    Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка — например,
    os_prod_list, os_name_list, os_code_list, os_type_list. В этой же функции создать главный список для хранения
    данных отчета — например, main_data — и поместить в него названия столбцов отчета в виде списка:
    «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения для этих столбцов также оформить
    в виде списка и поместить в файл main_data (также для каждого файла);

    Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой функции реализовать получение данных
    через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;

    Проверить работу программы через вызов функции write_to_csv().
"""
import csv
import re
from chardet import UniversalDetector

DETECTOR = UniversalDetector()
FILE_NAMES = ['info_1.txt', 'info_2.txt', 'info_3.txt']
PARAMS = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']


def get_regexp(param_list: list) -> list:
    """
    Функция оборачивает список строк по специальному шаблону и возвращает список регулярных выражений
    :param param_list: список строк
    :return: list
    """
    regexp_list = []
    for param in param_list:
        param = rf'({param}:\s+)(.+)'
        regexp_list.append(param)
    return regexp_list


def get_data(file_names_list: list) -> dict:
    """
    Функция принимает список имён файлов, определяет их кодировку и извлекает данные по списку регулярных выражений.
    Возвращает словарь списков.
    :param file_names_list: список имён файлов
    :return: dict
    """
    lists = {
        'os_prod_list': [],
        'os_name_list': [],
        'os_code_list': [],
        'os_type_list': [],
    }

    for file_name in file_names_list:
        with open(file_name, 'rb') as file:
            for i in file:
                DETECTOR.feed(i)
                if DETECTOR.done:
                    break
            DETECTOR.close()
        encoding = DETECTOR.result['encoding']

        with open(file_name, 'r', encoding=encoding) as file:
            content = file.read()

        regexps = get_regexp(PARAMS)
        matches = []
        for regexp in regexps:
            match = re.search(regexp, content)
            matches.append(match[2])

        for i, e in enumerate(lists):
            lists[e].append(matches[i])

    return lists


def write_to_csv() -> None:
    """
    Функция принимает данные и подготавливает их к записи в формате .csv
    :return: None
    """
    data = get_data(FILE_NAMES)
    with open('data_report.csv', 'w', encoding='utf-8', newline='') as file:
        file_writer = csv.writer(file)
        file_writer.writerow(PARAMS)

        for i in range(len(FILE_NAMES)):
            row = []
            for key in data.keys():
                row.append(data[key][i])
            file_writer.writerow(row)


if __name__ == '__main__':
    write_to_csv()

    # with open('data_report.csv', encoding='utf-8') as f_n:
    #     LINES = csv.reader(f_n)
    #     for row in LINES:
    #         print(row)
