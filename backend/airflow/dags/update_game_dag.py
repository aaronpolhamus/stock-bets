from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG
from datetime import datetime

from backend.logic.games import refresh_game_data


dag = DAG(
    dag_id='update_game_dag',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None
)


def refresh_game_with_context(ds, **kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    refresh_game_data(game_id)


run_this = PythonOperator(
    task_id='run_this',
    provide_context=True,
    python_callable=refresh_game_with_context,
    dag=dag)
