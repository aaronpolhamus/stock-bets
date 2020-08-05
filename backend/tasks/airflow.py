"""This module has some helper functions for working with externally triggered DAGs. Though it would be nice to locate
this code in the backend/airflow directory, it turns out that we basically need to leave this directory alone apart from
putting tests and DAGs in it according to airflow's specifications
"""
from typing import List
import random
import time

from airflow.api.client.local_client import Client
from airflow.models.dagrun import DagRun

afc = Client(None, None)


def log_headline(keys: tuple, values: List):
    headline_ls = [f"{key} = {value}" for key, value in zip(keys, values)]
    print("\n \n*** ARGUMENTS ***\n-----------------\n" + ", ".join(headline_ls) + "\n-----------------\n")


def context_parser(context: dict, *args: str):
    """*args looks for an inventory of names from the context that we expect a given task to have access to. Use of
    the .get access method means that misses names will default to None rather than generate a key error"""
    return_values = [context['dag_run'].conf.get(arg) for arg in args]
    log_headline(args, return_values)
    return return_values


def get_dag_run_state(dag_id: str, run_id: str):
    return DagRun.find(dag_id=dag_id, run_id=run_id)[0].state


def trigger_dag(dag_id: str, **kwargs):
    run_id = '%030x' % random.randrange(16**30)
    afc.trigger_dag(dag_id, run_id=run_id, conf=kwargs)
    while get_dag_run_state(dag_id, run_id) == "running":
        time.sleep(1)
        continue
    return get_dag_run_state(dag_id, run_id)
