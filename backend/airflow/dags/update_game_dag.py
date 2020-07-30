import time

from airflow.operators.python_operator import PythonOperator
from airflow.models import DAG
from datetime import datetime

from backend.logic.base import get_active_game_user_ids
from backend.logic.games import refresh_game_data
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
    pass


def make_metrics_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    calculate_and_pack_game_metrics(game_id)


def make_leaderboard_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    compile_and_pack_player_leaderboard(game_id)


def make_field_chart_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    make_the_field_charts(game_id)


def refresh_order_details_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        print(f"updating order details for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_order_details(game_id, user_id)


def refresh_portfolio_details_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        print(f"updating portfolio details for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_portfolio_details(game_id, user_id)


def make_order_performance_chart_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        print(f"updating order performance chart for user_id {user_id} out of [{', '.join(user_ids)}]")
        serialize_and_pack_order_performance_chart(game_id, user_id)


def log_multiplayer_winners_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    current_time = kwargs['dag_run'].conf['current_time']
    log_winners(game_id, current_time)


def make_winners_table_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    serialize_and_pack_winners_table(game_id)


def refresh_game_with_context(**kwargs):
    game_id = kwargs['dag_run'].conf['game_id']
    refresh_game_data(game_id)


run_this = PythonOperator(
    task_id='run_this',
    provide_context=True,
    python_callable=refresh_game_with_context,
    dag=dag)
