from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.models import DAG
from datetime import datetime

from backend.logic.base import get_active_game_user_ids
from backend.logic.visuals import (
    make_the_field_charts,
    compile_and_pack_player_leaderboard,
    calculate_and_pack_game_metrics,
    serialize_and_pack_order_details,
    serialize_and_pack_portfolio_details,
    serialize_and_pack_order_performance_chart,
    serialize_and_pack_winners_table
)
from backend.logic.metrics import log_winners


dag = DAG(
    dag_id='update_game_dag',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None
)


def update_balances_and_prices_cache_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    pass


def make_metrics_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    calculate_and_pack_game_metrics(game_id)


def make_leaderboard_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    compile_and_pack_player_leaderboard(game_id)


def update_field_chart_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    make_the_field_charts(game_id)


def refresh_order_details_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        # print(f"updating order details for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_order_details(game_id, user_id)


def refresh_portfolio_details_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        # print(f"updating portfolio details for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_portfolio_details(game_id, user_id)


def make_order_performance_chart_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        # print(f"updating order performance chart for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_order_performance_chart(game_id, user_id)


def log_multiplayer_winners_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    # current_time = kwargs['dag_run'].conf['current_time']
    import time
    log_winners(game_id, time.time())


def make_winners_table_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    serialize_and_pack_winners_table(game_id)


start_task = DummyOperator(
    task_id="start",
    dag=dag
)


update_balance_and_prices_cache = PythonOperator(
    task_id='update_balance_and_prices_cache',
    provide_context=True,
    python_callable=update_balances_and_prices_cache_with_context,
    dag=dag
)


make_metrics = PythonOperator(
    task_id='make_metrics',
    provide_context=True,
    python_callable=make_metrics_with_context,
    dag=dag
)


make_leaderboard = PythonOperator(
    task_id='make_leaderboard',
    provide_context=True,
    python_callable=make_leaderboard_with_context,
    dag=dag
)


update_field_chart = PythonOperator(
    task_id='update_field_chart',
    provide_context=True,
    python_callable=update_field_chart_with_context,
    dag=dag
)


refresh_order_details = PythonOperator(
    task_id='refresh_order_details',
    provide_context=True,
    python_callable=refresh_order_details_with_context,
    dag=dag
)


refresh_portfolio_details = PythonOperator(
    task_id='refresh_portfolio_details',
    provide_context=True,
    python_callable=refresh_portfolio_details_with_context,
    dag=dag
)


make_order_performance_chart = PythonOperator(
    task_id='make_order_performance_chart',
    provide_context=True,
    python_callable=make_order_performance_chart_with_context,
    dag=dag
)


log_multiplayer_winners = PythonOperator(
    task_id='log_multiplayer_winners',
    provide_context=True,
    python_callable=log_multiplayer_winners_with_context,
    dag=dag
)


make_winners_table = PythonOperator(
    task_id='make_winners_table',
    provide_context=True,
    python_callable=make_winners_table_with_context,
    dag=dag
)


end_task = DummyOperator(
    task_id="end",
    dag=dag
)

start_task >> update_balance_and_prices_cache >> make_metrics >> make_leaderboard >> update_field_chart >> end_task
start_task >> refresh_order_details >> end_task
start_task >> refresh_portfolio_details >> end_task
start_task >> make_order_performance_chart >> end_task
start_task >> log_multiplayer_winners >> make_winners_table >> end_task
