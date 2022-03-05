import argparse
import configparser
import os
import socket
import sys
import select
import threading
import time
import logging
import project.logs.server_log_config

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from project.common.variables import *
from project.common.utils import get_message, send_message
from project.common.decorators import log
from project.server.database import ServerDB
from project.server.core import MessageProcessor
from project.server.main_window import MainWindow

LOGGER = logging.getLogger('server')


@log
def parse_args(default_port, default_address):
    LOGGER.debug(f'Initializing the command line argument parser: {sys.argv}')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    parser.add_argument('--no_gui', action='store_true')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    LOGGER.debug('Arguments loaded successfully.')
    return listen_address, listen_port, gui_flag


@log
def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if SETTINGS in config:
        return config
    else:
        config.add_section(SETTINGS)
        config.set(SETTINGS, 'default_port', str(DEFAULT_PORT))
        config.set(SETTINGS, 'listen_address', '')
        config.set(SETTINGS, 'database_path', '')
        config.set(SETTINGS, 'database_file', 'srv_db.db3')
        return config


@log
def main():
    config = config_load()
    listen_address, listen_port, gui_flag = \
        parse_args(config[SETTINGS]['default_port'], config[SETTINGS]['listen_address'])

    database = ServerDB(os.path.join(config[SETTINGS]['database_path'], config[SETTINGS]['database_file']))

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input("Введите 'exit' для завершения работы сервера.")
            if command == 'exit':
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        server_app.exec_()
        server.running = False


if __name__ == '__main__':
    main()
