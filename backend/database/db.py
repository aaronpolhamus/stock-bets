from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from config import Config

db = SQLAlchemy()


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
db_metadata = MetaData(bind=engine, reflect=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
