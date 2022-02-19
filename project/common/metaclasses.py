import dis


class ServerMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        methods_global = []
        methods = []
        attrs = []

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    # print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods_global:
                            methods_global.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        # print(methods_global)
        # print(methods)

        if 'connect' in methods:
            raise TypeError('Using "connect" method is not allowed in server class.')

        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Incorrect socket initialization.')

        super().__init__(clsname, bases, clsdict)


class ClientMaker(type):
    def __init__(cls, clsname, bases, clsdict):
        methods = []

        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('Using restricted methods detected.')

        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('No socket function calls.')
        super().__init__(clsname, bases, clsdict)
