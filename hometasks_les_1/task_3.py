"""
3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
    Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
    (использовать модуль tabulate). Таблица должна состоять из двух колонок.
"""
from hometasks_les_1.task_1 import host_ping, HOSTS_LIST
from hometasks_les_1.task_2 import host_range_ping
from tabulate import tabulate


def host_range_ping_tab():
    nodes = host_range_ping(True)
    print(tabulate(nodes, headers='keys', tablefmt='grid', stralign='right'))


def host_range_ping_tab_2():
    nodes = host_ping(HOSTS_LIST, True)
    print(tabulate(nodes, headers='keys', tablefmt='pipe', stralign='center'))


if __name__ == '__main__':
    host_range_ping_tab()
    host_range_ping_tab_2()
