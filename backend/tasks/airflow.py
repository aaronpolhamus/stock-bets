"""This module has some helper functions for working with externally triggered DAGs. Though it would be nice to locate
this code in the backend/airflow directory, it turns out that we basically need to leave this directory alone apart from
putting tests and DAGs in it according to airflow's specifications
"""
from typing import List
import random
import time

from backend.database.db import engine
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


def handle_multiple_run_timestamps():
    """a necessary (hopefully temporary) hack to prime MySQL to log airflow tasks:
    https://stackoverflow.com/questions/52859113/in-apache-airflow-tool-dag-wont-run-due-to-duplicate-entry-problem-in-task-inst"""
    with engine.connect() as conn:
        conn.execute("USE airflow;")
        conn.execute("""
        ALTER TABLE `task_instance` 
        CHANGE `execution_date` `execution_date` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);""")


def trigger_dag(dag_id: str, wait_for_complete: bool = False, **kwargs):
    run_hash = '%030x' % random.randrange(16**30)
    kwarg_list = [f"{str(k)}:{str(v)}" for k, v in kwargs.items()]
    run_id = f"{run_hash}-{'_'.join(kwarg_list)}"
    handle_multiple_run_timestamps()
    afc.trigger_dag(dag_id, run_id=run_id, conf=kwargs)
    while wait_for_complete and get_dag_run_state(dag_id, run_id) == "running":
        time.sleep(1)
        continue
    return get_dag_run_state(dag_id, run_id)
