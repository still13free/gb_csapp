import sys
import logging
import project.logs.config_client_log
import project.logs.config_server_log
import inspect

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func):
    """
    Декоратор, выполняющий логирование вызовов функций.
    Сохраняет события типа debug, содержащие информацию:
    - об имени вызываемой функции,
    - параметрах, с которыми она вызывается,
    - файле, из которого была вызвана функция,
    - полный путь к этому файлу.
    """

    def wrap(*args, **kwargs):
        res = func(*args, **kwargs)
        LOGGER.debug(f'Function "{func.__name__}" was called with parameters: {args}, {kwargs} '
                     f'from function "{inspect.stack()[1][3]}" in file {inspect.stack()[1][1].split("/")[-1]}. '
                     f'Full path: "{inspect.stack()[1][1]}".')
        LOGGER.debug(f'Функция "{func.__name__}" была вызвана с параметрами: {args}, {kwargs} '
                     f'из функции "{inspect.stack()[1][3]}" внутри файла {inspect.stack()[1][1].split("/")[-1]}. '
                     f'Полный путь к файлу: "{inspect.stack()[1][1]}".')
        return res

    return wrap

# TODO: ?
# def login_required(func):
#     """
#     Декоратор, проверяющий, что клиент авторизован на сервере.
#     Проверяет, что передаваемый объект сокета находится в списке авторизованных клиентов,
#     за исключением передачи словаря-запроса на авторизацию.
#     Если клиент не авторизован, генерирует исключение TypeError
#     """
#
#     def checker(*args, **kwargs):
#         from project.server.core import MessageProcessor
#         from project.common.variables import ACTION, PRESENCE
#         if isinstance(args[0], MessageProcessor):
#             found = False
#             for arg in args:
#                 if isinstance(arg, socket.socket):
#                     # Проверяем, что данный сокет есть в списке names класса
#                     # MessageProcessor
#                     for client in args[0].names:
#                         if args[0].names[client] == arg:
#                             found = True
#
#             # Теперь надо проверить, что передаваемые аргументы не presence
#             # сообщение. Если presenсe, то разрешаем
#             for arg in args:
#                 if isinstance(arg, dict):
#                     if ACTION in arg and arg[ACTION] == PRESENCE:
#                         found = True
#             # Если не не авторизован и не сообщение начала авторизации, то
#             # вызываем исключение.
#             if not found:
#                 raise TypeError
#         return func(*args, **kwargs)
#
#     return checker
