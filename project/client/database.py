import os
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker


class ClientDB:
    """
    Класс-оболочка для работы с базой данных клиента.
    Используется база данных SQLite, реализованная с помощью SQLAlchemy ORM.
    """

    class AllUsers:
        """
        Класс-отображение таблицы всех пользователей.
        """

        def __init__(self, username):
            self.id = None
            self.username = username

    class Contacts:
        """
        Класс-отображение таблицы контактов.
        """

        def __init__(self, username):
            self.id = None
            self.username = username

    class MessageStat:
        """
        Класс-отображение статистики обмена сообщениями.
        """

        def __init__(self, username, direction, message):
            self.id = None
            self.username = username
            self.direction = direction
            self.message = message
            self.date = datetime.now()

    def __init__(self, nickname):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'db\\client_{nickname}.db3'
        self.db_engine = create_engine(
            f'sqlite:///{os.path.join(path, filename)}',
            echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False}
        )
        self.metadata = MetaData()

        users = Table('users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String),
                      )
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('username', String, unique=True),
                         )
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('username', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('date', DateTime),
                        )
        self.metadata.create_all(self.db_engine)

        mapper(self.AllUsers, users)
        mapper(self.Contacts, contacts)
        mapper(self.MessageStat, history)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        self.clear_contacts()
        self.session.commit()

    def add_users(self, users_list):
        """Метод, заполняющий таблицу всех пользователей."""
        self.session.query(self.AllUsers).delete()
        for user in users_list:
            user_row = self.AllUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def add_contact(self, contact):
        """Метод, добавляющий контакт в базу данных."""
        if not self.session.query(self.Contacts).filter_by(username=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """Метод, удаляющий определённый контакт из базы данных."""
        self.session.query(self.Contacts).filter_by(username=contact).delete()

    def clear_contacts(self):
        """Метод, полностью очищающий таблицу контактов."""
        self.session.query(self.Contacts).delete()

    def log_message(self, contact, direction, message):
        """Метод, сохраняющий сообщение в базе данных."""
        message_row = self.MessageStat(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_history(self, contact):
        """Метод, возвращающий историю сообщений с определённым пользователем."""
        query = self.session.query(self.MessageStat).filter_by(username=contact)
        return [
            (history_row.username,
             history_row.direction,
             history_row.message,
             history_row.date)
            for history_row in query.all()
        ]

    def get_users(self):
        """Метод, возвращающий список всех пользователей."""
        return [
            user[0] for user in self.session.query(self.AllUsers.username).all()
        ]

    def get_contacts(self):
        """Метод, возвращающий список контактов текущего пользователя."""
        return [
            contact[0] for contact in self.session.query(self.Contacts.username).all()
        ]

    def check_user(self, user):
        """Метод, проверяющий, существует ли пользователь."""
        return True if self.session.query(self.AllUsers).filter_by(username=user).count() else False

    def check_contact(self, contact):
        """Метод, проверяющий, существует ли контакт."""
        return True if self.session.query(self.Contacts).filter_by(username=contact).count() else False


if __name__ == '__main__':
    pass
