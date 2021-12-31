"""
2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах.
    Написать скрипт, автоматизирующий его заполнение данными. Для этого:

    Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item), количество (quantity),
    цена (price), покупатель (buyer), дата (date). Функция должна предусматривать запись данных в виде словаря в файл
    orders.json. В этом словаре параметров обязательно должны присутствовать юникод-символы, отсутствующие в кодировке
    ASCII. При записи данных указать величину отступа в 4 пробельных символа;

    Необходимо также установить возможность отображения символов юникода: ensure_ascii=False;

    Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра.
"""
import json
from chardet import detect


def write_order_to_json(item, quantity, price, buyer, date) -> None:
    """
    Функция принимает данные о товаре, его количестве, цене, покупателе, дате покупки и дописывает их в список заказов.
    :param item: товар
    :param quantity: количество
    :param price: цена
    :param buyer: покупатель
    :param date: дата
    :return: None
    """
    order = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date,
    }
    orders = 'orders.json'

    content = json.loads(read_data(orders))
    content['orders'].append(order)
    with open(orders, 'w', encoding='utf-8') as file:
        json.dump(content, file, indent=4, ensure_ascii=False)


def read_data(file_name='order.txt') -> str:
    """
    Функция принимает имя файла, определяет его кодировку и возвращает содержимое в виде строки.
    :param file_name: имя файла
    :return: str
    """
    with open(file_name, 'rb') as file:
        content = file.read()
    encoding = detect(content)['encoding']
    with open(file_name, 'r', encoding=encoding) as file:
        content = file.read()
    return content


if __name__ == '__main__':
    data = read_data().split('|')
    write_order_to_json(data[0], data[1], data[2], data[3], data[4])
