from subprocess import Popen, CREATE_NEW_CONSOLE

processes = []

while True:
    print()
    action = input("Choose action:\n\t!l - launch server & clients\n\t!x - close all windows\n\t!q - quit\n")

    if action == '!l':
        try:
            listen_clients = int(input('Listen clients count: '))
            send_clients = int(input('Send clients count: '))

            processes.append(Popen('python server.py', creationflags=CREATE_NEW_CONSOLE))
            for _ in range(listen_clients):
                processes.append(Popen('python client.py -m listen', creationflags=CREATE_NEW_CONSOLE))
            for _ in range(send_clients):
                processes.append(Popen('python client.py -m send', creationflags=CREATE_NEW_CONSOLE))
        except ValueError:
            print('*' * 43)
            print('WARNING: Number of clients must be integer!')
            print('*' * 43)
            continue

    elif action == '!x':
        while processes:
            process = processes.pop()
            process.kill()

    elif action == '!q':
        break
