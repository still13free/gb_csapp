import argparse
import os
import sys
import logging
import project.logs.config_client_log

from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from project.common.variables import *
from project.common.errors import ServerError
from project.common.decorators import log
from project.client.database import ClientDB
from project.client.transport import ClientTransport
from project.client.main_window import ClientMainWindow
from project.client.auth import AuthDialog

LOGGER = logging.getLogger('client')


@log
def parse_args():
    """
    Функция, разбирающая аргументы командной строки.
    Возвращает кортеж из четырёх элементов: адрес и порт сервера, имя и пароль пользователя.
    Проверяет корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Attempting to launch client with wrong port number: {server_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Client terminates.')
        LOGGER.critical(f'Попытка запуска клиента с некорректным номером порта: {server_port}. '
                        f'Допустимы номера с 1024 по 65535.'
                        f'Завершение работы.')
        sys.exit(1)
    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    server_address, server_port, client_name, client_passwd = parse_args()
    LOGGER.debug('Args loaded.')
    LOGGER.debug('Аргументы получены.')

    client_app = QApplication(sys.argv)
    authDialog = AuthDialog()
    if not client_name or not client_passwd:
        client_app.exec()
        if authDialog.startMainApp:
            client_name = authDialog.ui.nickname.text()
            client_passwd = authDialog.ui.password.text()
            LOGGER.debug(f"Authorization: nickname = '{client_name}', password = '{client_passwd}'.")
            LOGGER.debug(f"Авторизация: имя пользователя = '{client_name}', пароль = '{client_passwd}'.")
        else:
            sys.exit(0)

    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, '
                f'port - {server_port}, '
                f'username - {client_name}.')
    LOGGER.info(f'Клиент запущен с параметрами: '
                f'адрес сервера - {server_address}, '
                f'порт - {server_port}, '
                f'имя пользователя - {client_name}.')

    dir_path = os.getcwd()
    key_file = os.path.join(dir_path, f'keys\\{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as kf:
            kf.write(keys.export_key())
    else:
        with open(key_file, 'rb') as kf:
            keys = RSA.import_key(kf.read())
    keys.publickey().export_key()
    LOGGER.debug('Keys successfully loaded.')
    LOGGER.debug('Ключи успешно загружены.')

    database = ClientDB(client_name)
    try:
        transport = ClientTransport(server_address, server_port, database,
                                    client_name, client_passwd, keys)
        LOGGER.debug('Keys successfully loaded.')
        LOGGER.debug('Ключи успешно загружены.')
    except ServerError as err:
        message = QMessageBox()
        message.critical(authDialog, 'Ошибка сервера!', err.text)
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    del authDialog
    main_window = ClientMainWindow(database, transport, keys)
    client_app.exec()

    transport.shutdown()
    transport.join()
