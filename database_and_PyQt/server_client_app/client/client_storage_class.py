import datetime

from sqlalchemy import Column, create_engine, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker


class ClientStorage:
    Base = declarative_base()

    class KnownUsers(Base):
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)

    class MessageHistory(Base):
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        destination = Column(String)
        user = Column(String)
        message = Column(Text)
        date = Column(DateTime)

    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String)

    def __init__(self, username):
        self.username = username
        self.engine = create_engine(f'sqlite:///client/client_{username}.db3', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(name=contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(username=user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, destination, user, message):
        message_row = self.MessageHistory(
            destination=destination,
            user=user,
            message=message,
            date=datetime.datetime.now()
        )
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_user_history(self, user):
        query = self.session.query(self.MessageHistory).filter_by(user=user)
        return [(history_row.user, history_row.destination, history_row.message, history_row.date)
                for history_row in query.all()]
