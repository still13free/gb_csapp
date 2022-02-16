import logging

LOGGER = logging.getLogger('server')


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOGGER.critical(f'Attempting to launch server with wrong port number: {value}. '
                            f'Port number must be integer in range [1024, 65535]. '
                            f'Server terminates.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
