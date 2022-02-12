"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться должен только последний
    октет каждого адреса. По результатам проверки должно выводиться соответствующее сообщение.
"""
from hometasks_les_1.task_1 import host_ping
from ipaddress import ip_address


def host_range_ping(silent=False):
    while True:
        start_ip = input('Enter start ip-address: ')
        try:
            ipv4 = ip_address(start_ip)
            break
        except ValueError:
            print('Incorrect ip-address')

    while True:
        count = input('Enter count ip-addresses: ')
        if not count.isdigit():
            print('Count must me positive integer number')
        else:
            count = int(count)
            last_oct = int(start_ip.split('.')[3])
            if not (last_oct + count) <= 256:
                print('Only last octet may be changed')
                print(f'For {start_ip} max count is {256 - last_oct}')
            else:
                hosts = [str(ipv4 + i) for i in range(count)]
                break
    return host_ping(hosts, silent)


if __name__ == '__main__':
    host_range_ping()
