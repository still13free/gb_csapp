import argparse
import sys
import logging
import project.logs.client_log_config

from PyQt5.QtWidgets import QApplication
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
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        LOGGER.critical(f'Attempting to launch client with wrong port number: {server_port}. '
                        f'Port number must be integer in range [1024, 65535]. '
                        f'Client terminates.')
        sys.exit(1)
    return server_address, server_port, client_name


if __name__ == '__main__':
    server_address, server_port, client_name = parse_args()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.start_pressed:
            client_name = start_dialog.username.text()
            del start_dialog
        else:
            exit(0)

    LOGGER.info(f'Launched client with parameters: '
                f'server address - {server_address}, '
                f'port - {server_port}, '
                f'username - {client_name}.')

    database = ClientDB(client_name)

    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
