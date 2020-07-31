"""This module has some helper functions for working with externally triggered DAGs. Though it would be nice to locate
this code in the backend/airflow directory, it turns out that we basically need to leave this directory alone apart from
putting tests and DAGs in it according to airflow's specifications
"""

from airflow.api.client.local_client import Client

afc = Client(None, None)


def context_parser(context: dict, *args: str):
    """*args looks for an inventory of names from the context that we expect a given task to have access to. Use of
    the .get access method means that misses names will default to None rather than generate a key error"""
    return [context.get(arg) for arg in args]


def trigger_dag(dag_id: str, **kwargs):
    """triggers an externally-called dag run, passing in the parameters listed in **kwargs as DAG context. Returns
    True upon successful completion, False otherwise"""
    pass
