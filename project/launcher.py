from subprocess import Popen, CREATE_NEW_CONSOLE

processes = []

while True:
    print()
    action = input("Choose action:"
                   "\n\t!l - launch server & clients"
                   "\n\t!x - close all windows"
                   "\n\t!q - quit\n")

    if action == '!l':
        try:
            clients = int(input('Clients count: '))
            processes.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))
            for i in range(clients):
                processes.append(Popen(f'python client.py -n test{i}', creationflags=CREATE_NEW_CONSOLE))
        except ValueError:
            print('*' * 43)
            print('WARNING: Number of clients must be integer!')
            print('*' * 43)
            continue

    elif action == '!x':
        while processes:
            processes.pop().kill()

    elif action == '!q':
        break
