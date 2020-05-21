"""A collection of helper functions that wraps common database operations using the sqlalchemy ORM
"""
import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData
from config import Config


def retrieve_meta_data(engine):
    """Retrive metadata that can be used to instantiate table references with the sqlalchemy ORM
    """
    metadata = MetaData()
    metadata.reflect(engine)
    return metadata


def reset_db():
    # first we drop the main db and restart it in order to reset all auto-incrementing IDs
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    engine.execute("DROP DATABASE main;")
    engine.execute("CREATE DATABASE main;")
    os.system("flask db upgrade")


def unpack_enumerated_field_mappings(enum_class):
    """This function unpacks the natural language descriptions of each enumerated field so that these can be passed
    to the frontend in more readable forms. key-value pairs are preserved, and the keys are what actually get written
    to DB.
    """
    return {x.name: x.value for x in enum_class}


def orm_row_to_dict(row):
    """This takes a row selected from using the SQLAlchemy ORM and maps it into a dictionary. This is, surprisingly, not
    something that's supported out of the box in an intuitive way as far as I can tell
    """
    column_names = [column["name"] for column in row.column_descriptions]
    return {name: row.value(name) for name in column_names}


def make_db_session(engine):
    """Quick wrapper to save ourselves some extra lines and imports
    """
    Session = sessionmaker(bind=engine)
    return Session()


def table_updater(conn, table_orm, **kwargs):
    """Generic wrapper for updating data tables. kwargs are key-value pairings that map to columns in the table
    """
    return conn.execute(table_orm.insert(), kwargs)
