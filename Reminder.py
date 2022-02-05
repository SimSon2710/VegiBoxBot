from sqlalchemy import Column, String, Integer
from typing import List
from SqlConnector import SqlConnector, Base

"""
The Reminder object inherits from sqlalchemy.orm.declarative_base and so is use-able for the sqlalchemy orm features.
To create the table (__tablename__) once the command Base.metadata.create_all(SqlConnector().engine) has to be run.
"""


class Reminder(Base):
    __tablename__ = "reminders"

    reminders_lst: List[super] = []

    chat_id = Column(String, primary_key=True)
    day_of_week = Column(Integer)
    hour = Column(Integer)
    minute = Column(Integer)
    box_name = Column(String)

    def __init__(self, chat_id: str, day_of_week: int, box_name: str, hour: int, minute: int) -> None:
        super().__init__()
        self.chat_id: str = chat_id
        self.day_of_week: int = day_of_week
        self.hour: int = hour
        self.minute: int = minute
        self.box_name: str = box_name

        if self in Reminder.reminders_lst:
            for i, fave in enumerate(Reminder.reminders_lst):
                if self == fave:
                    Reminder.reminders_lst[i] = self
        else:
            Reminder.reminders_lst.append(self)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Reminder):
            return NotImplemented
        return self.chat_id == o.chat_id

    @classmethod
    def get_from_chat_id(cls, chat_id: str):
        reminder = None
        with SqlConnector().Session as session:
            reminder = session.query(Reminder).filter_by(chat_id=chat_id).first()
        return reminder

    @classmethod
    def load_from_db(cls):
        with SqlConnector().Session as session:
            for reminder in session.query(Reminder):
                if not reminder in cls.reminders_lst:
                    cls.reminders_lst.append(reminder)
        return cls.reminders_lst

    @classmethod
    def insert_reminder(cls, chat_id: str, day_of_week: int, hour: int, minute:int, box_name: str):
        r = Reminder(chat_id=chat_id, day_of_week=day_of_week, hour=hour, minute=minute, box_name=box_name)
        with SqlConnector().Session.no_autoflush as session:
            session.merge(r)
            session.flush()
        return r

    @classmethod
    def remove_reminder(cls, chat_id: str):
        with SqlConnector().Session.no_autoflush as session:
            reminder = session.query(Reminder).filter(Reminder.chat_id == chat_id).first()
            if reminder:
                session.delete(reminder)
            session.flush()
        cls.load_from_db()

