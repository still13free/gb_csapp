import time
from datetime import datetime
from pprint import pprint
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker


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

    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        print(path)
        self.db_engine = create_engine(f'sqlite:///{path}',
                                       echo=False,
                                       pool_recycle=7200,
                                       connect_args={'check_same_thread': False},
                                       )
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
        users_contacts_table = Table('Users_contacts', self.metadata,
                                     Column('id', Integer, primary_key=True),
                                     Column('user', ForeignKey('All_users.id')),
                                     Column('contact', ForeignKey('All_users.id'))
                                     )

        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('All_users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )
        self.metadata.create_all(self.db_engine)

        mapper(self.AllUsers, all_users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UsersContacts, users_contacts_table)
        mapper(self.UsersHistory, users_history_table)

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
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

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

    def process_message(self, sender, recipient):
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1
        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def del_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def get_contacts(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        query = self.session.query(self.UsersContacts, self.AllUsers.name).filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContacts.contact == self.AllUsers.id)
        return [contact[1] for contact in query.all()]

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

    def message_history(self):
        return self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers).all()


if __name__ == '__main__':
    test_db = ServerDB('server_base.db3')
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    print(test_db.users_list())
    print(test_db.active_users_list())
    test_db.user_logout('McG2')
    print(test_db.login_history('re'))
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.del_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    print(test_db.message_history())

    # test_db = ServerDB()
    #
    # test_db.user_login('test_client_1', '192.168.2.13', 7535)
    # test_db.user_login('test_client_2', '192.168.2.255', 7777)
    # test_db.user_login('test_client_3', '192.168.2.48', 13928)
    # print()
    # print('active users')
    # pprint(test_db.active_users_list())
    # print()
    #
    # test_db.user_logout('test_client_2')
    # print()
    # print('active users after logout')
    # pprint(test_db.active_users_list())
    # print()
    # print('all users')
    # pprint(test_db.users_list())
    # print()
    #
    # time.sleep(3)
    # test_db.user_login('test_client_2', '192.168.2.1', 4848)
    # print()
    # print('all users')
    # pprint(test_db.users_list())
    # print()
    # print('login history')
    # pprint(test_db.login_history())
    # print()
    # print('login history for test_client_2')
    # pprint(test_db.login_history('test_client_2'))
    # print()
    # print('login history for unknown client')
    # pprint(test_db.login_history('unknown'))
