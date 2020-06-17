"""A collection of helper functions that wraps common database operations using the sqlalchemy ORM
"""
import json
import os
import pandas as pd
from typing import List

from backend.database.db import engine


def reset_db():
    with engine.connect() as conn:
        conn.execute("SET FOREIGN_KEY_CHECKS = 0;")
        res = conn.execute("SHOW TABLES;")
        tables = [x[0] for x in res]
        for table in tables:
            conn.execute(f"DROP TABLE IF EXISTS {table};")
        conn.execute("SET FOREIGN_KEY_CHECKS = 1;")
    os.system("flask db upgrade")


def unpack_enumerated_field_mappings(enum_class):
    """This function unpacks the natural language descriptions of each enumerated field so that these can be passed
    to the frontend in more readable forms. key-value pairs are preserved, and the keys are what actually get written
    to DB.
    """
    return {x.name: x.value for x in enum_class}


def jsonify_inputs(values: List):
    """If an array or dictionary is being passed as a value, assume that this is for a json field and convert it"""
    for i, value in enumerate(values):
        if type(value) in [dict, list]:
            values[i] = json.dumps(value)
    return values


def add_row(table_name, **kwargs):
    """Convenience wrapper for DB inserts
    """
    columns = list(kwargs.keys())
    values = jsonify_inputs(list(kwargs.values()))
    sql = f"""
        INSERT INTO {table_name} ({','.join(columns)})
        VALUES ({','.join(['%s'] * len(values))});
    """
    with engine.connect() as conn:
        result = conn.execute(sql, values)
    return result.lastrowid


def query_to_dict(sql_query, *args):
    """Takes a sql query and returns a single dictionary in the case of a single return value, or an array of dict
    values if there is more than one result. This wraps python, and you can pass in a series of args if needed
    """
    with engine.connect() as conn:
        results = pd.read_sql(sql_query, conn, params=[*args]).to_dict(orient="records")
    engine.dispose()
    if len(results) > 1:
        return results
    return results[0]
