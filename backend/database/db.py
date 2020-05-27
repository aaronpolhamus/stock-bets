from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from config import Config

# db object for flask applications
db = SQLAlchemy()

# db_session for creating scoped sessions for other applications that interact with the DB
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))
