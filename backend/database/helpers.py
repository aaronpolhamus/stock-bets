"""A collection of helper functions that wraps common database operations using the sqlalchemy ORM
"""
import json
import os

import boto3
import pandas as pd
from typing import List
from sqlalchemy import MetaData

from backend.database.db import engine
from backend.config import Config


def drop_all_tables():
    db_metadata = MetaData(bind=engine)
    db_metadata.reflect()
    db_metadata.drop_all()


def reset_db():
    drop_all_tables()
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
    values if there is more than one result. This wraps pandas, and you can pass in a series of args if needed
    """
    with engine.connect() as conn:
        return pd.read_sql(sql_query, conn, params=[*args]).to_dict(orient="records")


def aws_client(service='s3', region='us-east-1', endpoint_url: str = Config.AWS_ENDPOINT_URL):
    """endpoint_url is for when working in a local development context only. This variable should not be set in
    production
    """
    boto_config = {'service_name': service, 'endpoint_url': endpoint_url, 'region_name': region,
                   'aws_access_key_id': Config.AWS_ACCESS_KEY_ID, 'aws_secret_access_key': Config.AWS_SECRET_ACCESS_KEY}
    if endpoint_url is None:
        del boto_config['endpoint_url']
    client = boto3.client(**boto_config)
    return client


def write_table_cache(cache_table_name: str, df: pd.DataFrame, **identifiers):
    """cache_table_name is where we want to save the dataframe to. additional identifiers for the cache, such as game_id
    and user_id, are supplied as **identifiers keyword args
    """
    for key, value in identifiers.items():
        df[key] = value

    with engine.connect() as conn:
        df.to_sql(cache_table_name, conn, if_exists="append", index=False)


def read_table_cache(cache_table_name: str, start_time: float, end_time: float, **conditions):
    """time boundaries for the cache are always required. **conditions is a set of keyword args that can be used to
    define additional select conditions from the cache, such as game_id=x and user_id=y"""
    sql = f"""
        SELECT * FROM {cache_table_name}
        WHERE 
            timestamp >= %s AND
            timestamp <= %s
    """
    additional_conditions = []
    for key, value in conditions.items():
        additional_conditions.append(value)
        sql += f"AND {key} = %s \n"
    sql += ";"
    conditions = [start_time, end_time] + additional_conditions
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, index_col="id", params=conditions)
