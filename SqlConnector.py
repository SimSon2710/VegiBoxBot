import subprocess
from os import environ
from sqlalchemy.engine.base import Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# The Base statement is necessary for the orm features of sqlalchemy and so is once instantiated at this point but
# used by the different tables/object (e.g. UserFavorite)
Base = declarative_base()


class SqlConnector:
    engine: Engine = None
    Session: sessionmaker = sessionmaker(autoflush=True, autocommit=True)

    def __init__(self) -> None:
        if not SqlConnector.engine:
            SqlConnector.Session.configure(bind=SqlConnector.start_engine())
        self.Session: Session = SqlConnector.Session()

    @classmethod
    def start_engine(cls):
        # check whether working on server or local by checking for existent of env variable "IS_HEROKU"...
        # this env variable has to be set on the server!
        on_heroku = False
        if "IS_HEROKU" in environ:
            on_heroku = True
        # if on server (heroku) get db_url from environment variables
        if on_heroku:
            db_url = environ.get("DATABASE_URL")
        # if running local, do some string manipulation
        else:
            from dotenv import dotenv_values
            NAME = dotenv_values(r'Credentials.env')["APP_NAME"]
            # the absolut path of herok is needed if you run python locally in a virtual env
            command = ["C:\\Program Files\\heroku\\bin\\heroku.cmd", "config:get", "DATABASE_URL", "--app", NAME]
            raw_db_url = subprocess.Popen(command, stdout=subprocess.PIPE).stdout
            # Convert binary string to a regular string & remove the newline character
            db_url = raw_db_url.read().decode("ascii").strip()

        # Convert "postgres://<db_address>"  --> "postgresql+psycopg2://<db_address>" needed for SQLAlchemy
        db_url = "postgresql+psycopg2://" + db_url.lstrip("postgres://")
        cls.engine = create_engine(db_url, echo=True)

        return cls.engine

    # helper method to drop a table by name
    @classmethod
    def drop_table(cls, table_name):
        cls.engine.execute(f"DROP TABLE {table_name}")
