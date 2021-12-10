"""
Модуль класса базы данных сервера
"""


import datetime

from sqlalchemy import Column, create_engine, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from common.variables import DATABASE_SERVER


class ServerStorage:
    """
    Класс для серверной базы данных
    """

    Base = declarative_base()

    class Users(Base):
        """
        Класс модели таблицы пользователей
        """
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)
        last_login = Column(DateTime)
        passwd_hash = Column(String)
        pubkey = Column(Text)

    class ActiveUsers(Base):
        """
        Класс модели таблицы активных пользователей
        """
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

    class LoginHistory(Base):
        """
        Класс модели таблицы историзации входа пользователей
        """
        __tablename__ = 'login_history'
        id = Column(Integer, primary_key=True)
        name = Column(ForeignKey('users.id'))
        ip_address = Column(String)
        port = Column(Integer)
        date_time = Column(DateTime)

    class UsersContacts(Base):
        """
        Класс модели таблицы контактов пользователей
        """
        __tablename__ = 'users_contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        contact = Column(ForeignKey('users.id'))

    class UsersHistory(Base):
        """
        Класс модели таблицы истории сообщений
        """
        __tablename__ = 'history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('users.id'))
        sent = Column(Integer, default=0)
        accepted = Column(Integer, default=0)

    def __init__(self, db_path=DATABASE_SERVER):
        """
        Метод инициализации. В нём создаётся движок базы данных,
        создаются таблицы (при необходимости), объект сессии и очищается таблица активных пользователей.
        """
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False,
                                    pool_recycle=7200, connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def login_user(self, username, ip_address, port, key):
        """
        Метод для записи данных в базу о входе пользователя
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        login_time = datetime.datetime.now()

        if user:
            user.last_login = login_time
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        active_users = {
            'user': user.id,
            'ip_address': ip_address,
            'port': port,
            'login_time': login_time
        }

        history = {
            'name': user.id,
            'ip_address': ip_address,
            'port': port,
            'date_time': login_time
        }

        self.session.add_all([self.ActiveUsers(**active_users), self.LoginHistory(**history)])
        self.session.commit()

    def logout_user(self, username):
        """
        Метод, удаляющий запись из таблицы активных пользователей при выходе пользователя из чата
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.Users(name=name, passwd_hash=passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user=user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """
        Метод, удаляющий пользователя из базы.
        """
        user = self.session.query(self.Users).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(self.UsersContacts).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContacts).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(name=name).delete()
        self.session.commit()

    def users_all(self):
        """
        Метод получения всех записей из таблицы пользователей (только логины и дата последнего входа)
        """
        query = self.session.query(self.Users.name, self.Users.last_login)
        return query.all()

    def users_active(self):
        """
        Метод получения всех записей из таблицы активных пользователей
        """
        query = self.session.query(
            self.Users.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.Users)
        return query.all()

    def login_history(self, username=None):
        """
        Метод получения всех записей или записей по конкретному пользователю
        из таблицы историзации входа пользователей
        """
        query = self.session.query(
            self.Users.name,
            self.LoginHistory.date_time,
            self.LoginHistory.ip_address,
            self.LoginHistory.port
        ).join(self.Users)
        if username:
            query = query.filter(self.Users.name == username)
        return query.all()

    def process_message(self, sender, receiver):
        """
        Метод обновления количества полученных и отправленных сообщений в соотвествующих записях
        """
        sender_id = self.session.query(self.Users).filter_by(name=sender).first().id
        receiver_id = self.session.query(self.Users).filter_by(name=receiver).first().id
        sender_obj = self.session.query(self.UsersHistory).filter_by(user=sender_id).first()
        receiver_obj = self.session.query(self.UsersHistory).filter_by(user=receiver_id).first()
        sender_obj.sent += 1
        receiver_obj.accepted += 1
        self.session.commit()

    def add_contact(self, user, contact):
        """
        Метод добавления контакта
        """
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        if contact and not self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).all():
            contact_row = self.UsersContacts(user=user.id, contact=contact.id)
            self.session.add(contact_row)
            self.session.commit()

    def remove_contact(self, user, contact):
        """
        Метод удаления контакта
        """
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        if contact:
            self.session.query(self.UsersContacts).filter(
                self.UsersContacts.user == user.id,
                self.UsersContacts.contact == contact.id
            ).delete()
            self.session.commit()

    def get_contacts(self, username):
        """
        Метод получения списка контактов пользователя
        """
        user = self.session.query(self.Users).filter_by(name=username).first()

        query = self.session.query(
            self.UsersContacts, self.Users.name
        ).filter_by(user=user.id).join(
            self.Users,
            self.UsersContacts.contact == self.Users.id
        )
        return [contact[1] for contact in query.all()]

    def message_history(self):
        """
        Метод получения истории сообщений
        """
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Users)
        return query.all()

    def get_hash(self, name):
        """
        Метод получения хэша пароля пользователя.
        """
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """
        Метод получения публичного ключа пользователя.
        """
        user = self.session.query(self.Users).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        """
        Метод проверяющий существование пользователя.
        """
        if self.session.query(self.Users).filter_by(name=name).count():
            return True
        else:
            return False
