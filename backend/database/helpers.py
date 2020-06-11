"""A collection of helper functions that wraps common database operations using the sqlalchemy ORM
"""
import os
from sqlalchemy import create_engine, MetaData

from backend.database.db import db_session
from backend.config import Config


def retrieve_meta_data():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    return MetaData(bind=engine, reflect=True)


def represent_table(table_name):
    """It has been really challenging building a working handler for ORM table representations. A global metadata
    object, e.g. defined at the database.db level, gets corrupted easily as the database is operated on by the
    application. After a few days of trying, the best way to do this looks like an on-the-fly reflecting of the
    metadata in each case where we want to interact with a table
    """
    meta_data = retrieve_meta_data()
    return meta_data.tables[table_name]


def reset_db():
    db_metadata = retrieve_meta_data()
    db_metadata.drop_all()
    os.system("flask db upgrade")


def unpack_enumerated_field_mappings(enum_class):
    """This function unpacks the natural language descriptions of each enumerated field so that these can be passed
    to the frontend in more readable forms. key-value pairs are preserved, and the keys are what actually get written
    to DB.
    """
    return {x.name: x.value for x in enum_class}


def orm_rows_to_dict(row):
    """This takes a row selected from using the SQLAlchemy ORM and maps it into a dictionary. This is, surprisingly, not
    something that's supported out of the box in an intuitive way as far as I can tell
    """
    column_names = [column["name"] for column in row.column_descriptions]
    return {name: row.value(name) for name in column_names}


def table_updater(table, **kwargs):
    """Generic wrapper for updating data tables from ORM representations. kwargs are key-value pairings that map to
    columns in the table
    """
    with db_session.connection() as conn:
        result = conn.execute(table.insert(), kwargs)
        db_session.commit()
    return result
