"""
3. Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле
    YAML-формата. Для этого:

    Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число,
    третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом, отсутствующим в
    кодировке ASCII (например, €);

    Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. При этом обеспечить стилизацию файла
    с помощью параметра default_flow_style, а также установить возможность работы с юникодом: allow_unicode = True;

    Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""
import yaml


DATA = {
    'list': ['something', True, 7.62, None],
    'integer': 13,
    'dict': {
        'first': '1Ё',
        'second': '2Ʌ',
        'last': '0¥'
    }
}


def create_yaml_file(data: dict) -> None:
    """
    Функция принимает словарь данных и записывает его в yaml-файл.
    :param data: словарь данных
    :return: None
    """
    with open('file.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False, indent=4, allow_unicode=True)


def read_and_check(data: dict, file_name='file.yaml') -> None:
    """
    Функция сравнивает данные из словаря и из имя yaml-файла, в котороый они были записаны.
    :param data: исходный словарь данных
    :param file_name: имя yaml-файла
    :return: None
    """
    with open(file_name, 'r', encoding='utf-8') as file:
        content = yaml.load(file, Loader=yaml.FullLoader)
    print(data == content)


if __name__ == '__main__':
    create_yaml_file(DATA)
    read_and_check(DATA)
