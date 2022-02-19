import time
from datetime import datetime
from pprint import pprint
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker

from common.variables import SERVER_DATABASE


class ServerDB:
    class AllUsers:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_login = datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, ip, port, login_time):
            self.id = None
            self.user = user_id
            self.ip = ip
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, user_id, date_time, ip, port):
            self.id = None
            self.user = user_id
            self.date_time = date_time
            self.ip = ip
            self.port = port

    def __init__(self):
        self.db_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        all_users_table = Table('All_users', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('name', String, unique=True),
                                Column('last_login', DateTime),
                                )
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('All_users.id'), unique=True),
                                   Column('ip', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime),
                                   )
        login_history_table = Table('Login_history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('All_users.id')),
                                    Column('date_time', DateTime),
                                    Column('ip', String),
                                    Column('port', Integer),
                                    )
        self.metadata.create_all(self.db_engine)

        mapper(self.AllUsers, all_users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        print(f'<!> {username} login from {ip}:{port} <!>')

        u = self.session.query(self.AllUsers).filter_by(name=username)
        if u.count():
            user = u.first()
            user.last_login = datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        print(f'<!> {username} logout <!>')

        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        return self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        ).all()

    def active_users_list(self):
        return self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time,
        ).join(self.AllUsers).all()

    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip,
            self.LoginHistory.port,
        ).join(self.AllUsers)

        if username:
            user = self.session.query(self.AllUsers).filter_by(name=username)
            if not user.count():
                print(f"No users with name '{username}'!")
                return []
            query = query.filter(self.AllUsers.name == username)
        return query.all()


if __name__ == '__main__':
    test_db = ServerDB()

    test_db.user_login('test_client_1', '192.168.2.13', 7535)
    test_db.user_login('test_client_2', '192.168.2.255', 7777)
    test_db.user_login('test_client_3', '192.168.2.48', 13928)
    print()
    print('active users')
    pprint(test_db.active_users_list())
    print()

    test_db.user_logout('test_client_2')
    print()
    print('active users after logout')
    pprint(test_db.active_users_list())
    print()
    print('all users')
    pprint(test_db.users_list())
    print()

    time.sleep(3)
    test_db.user_login('test_client_2', '192.168.2.1', 4848)
    print()
    print('all users')
    pprint(test_db.users_list())
    print()
    print('login history')
    pprint(test_db.login_history())
    print()
    print('login history for test_client_2')
    pprint(test_db.login_history('test_client_2'))
    print()
    print('login history for unknown client')
    pprint(test_db.login_history('unknown'))
