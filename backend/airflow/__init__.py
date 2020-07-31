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
