"""
5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтового в строковый
    (предварительно определив кодировку выводимых сообщений).
"""

from chardet import detect
from subprocess import Popen, PIPE
from platform import system


def ping_urls(url_list: list, count=4):
    param = '-n' if system().lower() == 'windows' else '-c'
    for url in url_list:
        args = ['ping', param, str(count), url]
        ping = Popen(args, stdout=PIPE)
        for line in ping.stdout:
            report = detect(line)
            line = line.decode(report['encoding']).encode('utf-8')
            print(line.decode('utf-8'))


URLS = [
    'yandex.ru',
    'youtube.com',
]

ping_urls(URLS)
