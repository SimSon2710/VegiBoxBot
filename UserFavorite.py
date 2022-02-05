from sqlalchemy import Column, String
from AboBox import AboBox
from SqlConnector import SqlConnector, Base

"""
The UserFavorite object inherits from sqlalchemy.orm.declarative_base and so is use-able for the sqlalchemy orm 
features.
To create the table (__tablename__) once the command Base.metadata.create_all(SqlConnector().engine) has to be run.
"""


class UserFavorite(Base):
    __tablename__ = "user_faves"

    chat_id = Column(String, primary_key=True)
    box_name = Column(String)
    box_size = Column(String)

    def __init__(self, chat_id: str, box_name: str, box_size: str) -> None:
        super().__init__()
        self.chat_id: str = chat_id
        self.box_name: str = box_name
        self.box_size: str = box_size

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, UserFavorite):
            return NotImplemented
        return self.chat_id == o.chat_id

    @classmethod
    def set_from_query(cls, chat_id: str, box_name: str, box_size: str = ""):
        fave: UserFavorite = None
        for box in AboBox.boxes_lst:
            # replacements for german spellings
            if box_name.replace('ß', 'ss').lower() in box.name.replace('ß', 'ss').lower() and \
                    box_size.replace('ß', 'ss').lower() in box.size.replace('ß', 'ss').lower():
                fave = UserFavorite(chat_id=str(chat_id), box_name=box.name, box_size=box.size)
        if fave:
            with SqlConnector().Session.no_autoflush as session:
                session.merge(fave)
                session.flush()
            return fave.box_name
        else:
            return None

    @classmethod
    def get_from_chat_id(cls, chat_id: str):
        fave: UserFavorite = None
        with SqlConnector().Session as session:
            fave = session.query(UserFavorite).filter_by(chat_id=chat_id).first()
        return fave

    @classmethod
    def remove_user(cls, chat_id: str):
        with SqlConnector().Session.no_autoflush as session:
            user = session.query(UserFavorite).filter(UserFavorite.chat_id == chat_id).first()
            if user:
                session.delete(user)
            session.flush()
