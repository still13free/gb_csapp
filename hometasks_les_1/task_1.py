"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
    Аргументом функции является список, в котором каждый сетевой узел должен быть представлен
    именем хоста или ip-адресом.
    В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
    («Узел доступен», «Узел недоступен»).
    При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""
import time
from ipaddress import ip_address
from platform import system
from subprocess import Popen, PIPE

HOSTS_LIST = [
    '8.8.8.8',
    '0.13.0.0',
    '127.0.0.1',
    'google.com',
    '192.168.2.255',
    'yandex.ru',
]


def host_ping(hosts: list, silent=False):
    if silent:
        nodes = {
            'reachable': [],
            'unreachable': [],
        }

    param = '-n' if system().lower() == 'windows' else '-c'
    print('Trying to ping hosts list!')

    for host in hosts:
        try:
            time.sleep(1)
            ipv4 = ip_address(host)
        except ValueError:
            if not silent:
                print(f'{host} is not ip-address')
            ipv4 = host

        args = ['ping', param, '1', str(ipv4)]
        ping = Popen(args, stdout=PIPE)
        if ping.wait() == 0:
            if silent:
                nodes['reachable'].append(host)
            else:
                print(f'{host} - node is reachable')
        else:
            if silent:
                nodes['unreachable'].append(host)
            else:
                print(f'{host} - node is unreachable')
    if silent:
        return nodes


if __name__ == '__main__':
    host_ping(HOSTS_LIST)
