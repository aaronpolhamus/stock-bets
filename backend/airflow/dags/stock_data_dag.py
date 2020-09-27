from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow import DAG
from datetime import datetime

from backend.database.db import engine
from backend.logic.stock_data import (
    get_symbols_table,
    SeleniumDriverError,
    scrape_dividends,
    apply_dividends_to_stocks,
    scrape_stock_splits,
    apply_stock_splits,
    update_symbols
)


dag = DAG(
    dag_id='stock_data_dag',
    start_date=datetime(2000, 1, 1),
    schedule_interval=None
)


start_task = DummyOperator(
    task_id="start",
    dag=dag
)


end_task = DummyOperator(
    task_id="end",
    dag=dag
)


update_symbols_task = PythonOperator(
    task_id="update_symbols_task",
    python_callable=update_symbols,
    dag=dag
)


scrape_dividends_task = PythonOperator(
    task_id="scrape_dividends_task",
    python_callable=scrape_dividends,
    dag=dag
)


apply_dividends_task = PythonOperator(
    task_id="apply_dividends_task",
    python_callable=apply_dividends_to_stocks,
    dag=dag
)


scrape_stock_splits_task = PythonOperator(
    task_id="scrape_stock_splits_task",
    python_callable=scrape_stock_splits,
    dag=dag
)


apply_stock_splits_task = PythonOperator(
    task_id="apply_stock_splits_task",
    python_callable=apply_stock_splits,
    dag=dag
)


start_task >> update_symbols_task >> end_task
start_task >> scrape_stock_splits_task >> apply_stock_splits_task >> end_task
start_task >> scrape_dividends_task >> apply_dividends_task >> end_task
