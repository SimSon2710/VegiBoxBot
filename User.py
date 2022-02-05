from sqlalchemy import Column, String
from SqlConnector import SqlConnector, Base

"""
The User object inherits from sqlalchemy.orm.declarative_base and so is use-able for the sqlalchemy orm features.
To create the table (__tablename__) once the command Base.metadata.create_all(SqlConnector().engine) has to be run.

Users (chat_id, user_name) are only store to send them information about new updates.
"""


class User(Base):
    __tablename__ = "users"

    chat_id = Column(String, primary_key=True)
    name = Column(String)

    def __init__(self, chat_id: str, name: str) -> None:
        super().__init__()
        self.chat_id: str = chat_id
        self.name: str = name

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, User):
            return NotImplemented
        return self.chat_id == o.chat_id

    @classmethod
    def get_from_chat_id(cls, chat_id: str):
        user: User = None
        with SqlConnector().Session as session:
            user = session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            return user.chat_id, user.name
        else:
            return None

    @classmethod
    def load_users_from_db(cls):
        with SqlConnector().Session as session:
            return session.query(User)

    @classmethod
    def insert_user(cls, chat_id: str, name: str = None):
        with SqlConnector().Session.no_autoflush as session:
            session.merge(User(chat_id=chat_id, name=name))
            session.flush()

    @classmethod
    def remove_user(cls, chat_id: str):
        with SqlConnector().Session.no_autoflush as session:
            user = session.query(User).filter(User.chat_id == chat_id).first()
            if user:
                session.delete(user)
            session.flush()
