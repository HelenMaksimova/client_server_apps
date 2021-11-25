import datetime

from sqlalchemy import Column, create_engine, Integer, String, DateTime, ForeignKey
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

    def __init__(self, db_path=DATABASE_SERVER):
        """
        Метод инициализации. В нём создаётся движок базы данных,
        создаются таблицы (при необходимости), объект сессии и очищается таблица активных пользователей.
        """
        self.engine = create_engine(db_path, echo=False)
        self.Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def login_user(self, username, ip_address, port):
        """
        Метод для записи данных в базу о входе пользователя
        :param username: логин пользователя
        :param ip_address: ip-адрес
        :param port: порт
        :return: None
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        login_time = datetime.datetime.now()

        if user:
            user.last_login = login_time
        else:
            user = self.Users(name=username, last_login=login_time)
            self.session.add(user)
            self.session.commit()

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
        :param username: логин пользователя
        :return: None
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_all(self):
        """
        Метод получения всех записей из таблицы пользователей (только логины и дата последнего входа)
        :return: список кортежей
        """
        query = self.session.query(self.Users.name, self.Users.last_login)
        return query.all()

    def users_active(self):
        """
        Метод получения всех записей из таблицы активных пользователей
        :return: список кортежей
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
        :param username: логин пользователя
        :return: список кортежей
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


if __name__ == '__main__':
    db = ServerStorage()
    db.login_user('helen', '127.0.0.1', 8888)
    db.login_user('olga', '127.0.0.1', 8889)
    print('\nАктивные пользователи:')
    print(*db.users_active(), sep='\n')
    db.logout_user('helen')
    print('\nАктивные пользователи после выхода helen:')
    print(*db.users_active(), sep='\n')
    print('\nИстория входов всех пользователей:')
    print(*db.login_history(), sep='\n')
    print('\nИстория входов olga:')
    print(*db.login_history('olga'), sep='\n')
    print('\nВсе пользователи:')
    print(*db.users_all(), sep='\n')

