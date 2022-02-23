import time
from datetime import datetime
from pprint import pprint
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker


class ClientDB:
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, user_from, user_to, message):
            self.id = None
            self.user_from = user_from
            self.user_to = user_to
            self.message = message
            self.date_time = datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        self.db_engine = create_engine(f'sqlite:///cli_db_{name}.db3',
                                       echo=False,
                                       pool_recycle=7200,
                                       connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        known_users_table = Table('known_users', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('username', String),
                                  )
        message_history_table = Table('message_history', self.metadata,
                                      Column('id', Integer, primary_key=True),
                                      Column('user_from', String),
                                      Column('user_to', String),
                                      Column('message', Text),
                                      Column('date_time', DateTime),
                                      )
        contacts_table = Table('contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('name', String, unique=True),
                               )
        self.metadata.create_all(self.db_engine)

        mapper(self.KnownUsers, known_users_table)
        mapper(self.MessageHistory, message_history_table)
        mapper(self.Contacts, contacts_table)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        self.session.query(self.KnownUsers).delete()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_users(self, users_list):
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def log_message(self, user_from, user_to, message):
        message_row = self.MessageHistory(user_from, user_to, message)
        self.session.add(message_row)
        self.session.commit()

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        return True if self.session.query(self.KnownUsers).filter_by(username=user).count() else False

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def check_contact(self, contact):
        return True if self.session.query(self.Contacts).filter_by(name=contact).count() else False

    def get_history(self, user_from=None, user_to=None):
        query = self.session.query(self.MessageHistory)
        if user_from:
            query = query.filter_by(user_from=user_from)
        if user_to:
            query = query.filter_by(user_to=user_to)
        return [(history_row.user_from, history_row.user_to, history_row.message, history_row.date_time)
                for history_row in query.all()]

# if __name__ == '__main__':
#     test_db = ClientDB('test1')
#     for i in ['test3', 'test4', 'test5']:
#         test_db.add_contact(i)
#     test_db.add_contact('test4')
#     test_db.add_users(['test1', 'test2', 'test3', 'test4', 'test5'])
#     test_db.log_message('test1', 'test2', f'Привет! я тестовое сообщение от {datetime.now()}!')
#     test_db.log_message('test2', 'test1', f'Привет! я другое тестовое сообщение от {datetime.now()}!')
#     print(test_db.get_contacts())
#     print(test_db.get_users())
#     print(test_db.check_user('test1'))
#     print(test_db.check_user('test10'))
#     print(test_db.get_history('test2'))
#     print(test_db.get_history(user_to='test2'))
#     print(test_db.get_history('test3'))
#     test_db.del_contact('test4')
#     print(test_db.get_contacts())
