import argparse
import os
import sys
import logging
import project.logs.client_log_config

from PyQt5.QtWidgets import QApplication, QMessageBox
from project.common.variables import *
from project.common.errors import ServerError
from project.common.decorators import log
from project.client.database import ClientDB
from project.client.transport import ClientTransport
from project.client.main_window import ClientMainWindow
from project.client.start_dialog import UserNameDialog

LOGGER = logging.getLogger('client')


@log
def parse_args():
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
        sys.exit(1)
    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':
    server_address, server_port, client_name, client_passwd = parse_args()
    LOGGER.debug('Args loaded')
    client_app = QApplication(sys.argv)

    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            LOGGER.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)

    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, '
                f'port - {server_port}, '
                f'username - {client_name}.')

    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # key_file = os.path.join(dir_path, f'{client_name}.key')
    # if not os.path.exists(key_file):
    #     keys = RSA.generate(2048, os.urandom)
    #     with open(key_file, 'wb') as key:
    #         key.write(keys.export_key())
    # else:
    #     with open(key_file, 'rb') as key:
    #         keys = RSA.import_key(key.read())
    #
    # keys.publickey().export_key()
    LOGGER.debug("Keys successfully loaded.")

    database = ClientDB(client_name)

    try:
        transport = ClientTransport(server_address, server_port, database, client_name, client_passwd, keys)
        LOGGER.debug("Transport ready.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    del start_dialog

    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
