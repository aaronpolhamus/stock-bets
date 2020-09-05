#!/usr/bin/env bash
until nc -z -v -w30 $MYSQL_HOST $MYSQL_PORT
do
  echo "Waiting a second until" $MYSQL_HOST "is receiving connections on port" $MYSQL_PORT
  sleep 1
done

if [ $SERVICE == "api" ]; then
    # upgrade to the data model
    flask db upgrade

    # start the web application
    python wsgi.py
fi

if [ $SERVICE == "worker" ]; then
    nohup celery -A tasks.celery.celery worker --loglevel=info --concurrency=${CELERY_WORKER_CONCURRENCY} -n primary@%h &
    airflow worker --concurrency=${CELERY_WORKER_CONCURRENCY}
fi

if [ $SERVICE == "scheduler" ]; then
    celery -A tasks.celery.celery beat --loglevel=info
fi

if [ $SERVICE == "airflow" ]; then
    airflow initdb
    nohup airflow scheduler &
    rm -rf $AIRFLOW_HOME/airflow-webserver.pid
    nohup airflow webserver
fi
