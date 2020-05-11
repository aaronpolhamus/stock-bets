"""A collection of helper functions that wraps common database operations using the sqlalchemy ORM
"""
import os

from sqlalchemy import create_engine, MetaData
from config import Config


def retrieve_meta_data():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
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
