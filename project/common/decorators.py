import sys
import logging
import logs.client_log_config
import logs.server_log_config
import inspect

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func):
    def wrap(*args, **kwargs):
        res = func(*args, **kwargs)
        LOGGER.debug(f'Function "{func.__name__}" was called with parameters: {args}, {kwargs} '
                     f'from function "{inspect.stack()[1][3]}" in file {inspect.stack()[1][1].split("/")[-1]}. '
                     f'Full path: "{inspect.stack()[1][1]}".')
        return res

    return wrap
