import logging
import sys

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


class Port:
    """
    Класс-дескриптор для номера порта.
    Позволяет использовать только порты с 1023 по 65536.
    При попытке установить неподходящий номер порта генерирует исключение.
    """

    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOGGER.critical(f'Attempting to launch server with invalid port number: {value}. '
                            f'Port number must be integer in range [1024, 65535]. ')
            LOGGER.critical(f'Попытка запуска с указанием неподходящего порта {value}.'
                            f'Допустимы адреса с 1024 до 65535.')
            raise TypeError('Invalid port number / Некорректрый номер порта')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
