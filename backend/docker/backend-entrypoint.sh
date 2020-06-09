#!/usr/bin/env bash
until nc -z -v -w30 $MYSQL_HOST $MYSQL_PORT
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

# TODO refactor according to this pattern at some point: https://gist.github.com/mathop/37d817e720460b6689f9887b16e339f7

# would be ideal not to worry about this, since we use Chromium instead of Firefox, but the webscraping
# has been fragile due to versioning and this creates some redundancy
./docker/install_geckodriver.sh

if [ $SERVICE == "api" ]; then
    # upgrade to the data model
    flask db upgrade

    # start the web application
    python wsgi.py
fi

if [ $SERVICE == "worker" ]; then
    celery -A tasks.celery.celery worker --concurrency=20 --loglevel=info
fi

if [ $SERVICE == "scheduler" ]; then
    celery -A tasks.celery.celery beat --loglevel=info
fi
