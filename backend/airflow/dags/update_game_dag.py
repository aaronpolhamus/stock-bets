from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
from datetime import datetime

from backend.logic.base import (
    get_time_defaults,
    get_active_game_user_ids,
)
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
from backend.tasks.airflow import context_parser


dag = DAG(
    dag_id='update_game_dag',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None
)


def make_metrics_with_context(**context):
    game_id, start_time, end_time = context_parser(context, "game_id", "start_time", "end_time")
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    calculate_and_pack_game_metrics(game_id, start_time, end_time)


def make_leaderboard_with_context(**context):
    game_id, start_time, end_time = context_parser(context, "game_id", "start_time", "end_time")
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    compile_and_pack_player_leaderboard(game_id, start_time, end_time)


def update_field_chart_with_context(**context):
    game_id, start_time, end_time = context_parser(context, "game_id", "start_time", "end_time")
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    make_the_field_charts(game_id, start_time, end_time)


def refresh_order_details_with_context(**context):
    game_id, = context_parser(context, "game_id")
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        serialize_and_pack_order_details(game_id, user_id)


def refresh_portfolio_details_with_context(**context):
    game_id, = context_parser(context, "game_id")
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        serialize_and_pack_portfolio_details(game_id, user_id)


def make_order_performance_chart_with_context(**context):
    game_id, start_time, end_time = context_parser(context, "game_id", "start_time", "end_time")
    start_time, end_time = get_time_defaults(game_id, start_time, end_time)
    user_ids = get_active_game_user_ids(game_id)
    for user_id in user_ids:
        serialize_and_pack_order_performance_chart(game_id, user_id, start_time, end_time)


def log_multiplayer_winners_with_context(**context):
    game_id, start_time, end_time = context_parser(context, "game_id", "start_time", "end_time")
    _, end_time = get_time_defaults(game_id, start_time, end_time)
    log_winners(game_id, end_time)


def make_winners_table_with_context(**context):
    game_id, = context_parser(context, "game_id")
    serialize_and_pack_winners_table(game_id)


start_task = DummyOperator(
    task_id="start",
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

start_task >> make_order_performance_chart
make_order_performance_chart >> make_metrics >> make_leaderboard >> update_field_chart >> end_task
make_order_performance_chart >> log_multiplayer_winners >> make_winners_table >> end_task
start_task >> refresh_order_details >> end_task
start_task >> refresh_portfolio_details >> end_task

