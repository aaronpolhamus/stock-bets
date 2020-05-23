#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

# setup the chrome driver that we will use for webscraping
./docker/install_geckodriver.sh

# You can also embed beat inside the worker by enabling the workers -B option, this is convenient if you’ll never run
# more than one worker node, but it’s not commonly used and for that reason isn’t recommended for production use:
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
celery -A tasks.celery.celery worker --concurrency=20 --loglevel=info -B
