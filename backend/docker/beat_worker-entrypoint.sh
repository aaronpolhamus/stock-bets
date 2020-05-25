#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

# setup the chrome driver that we will use for webscraping
./docker/install_geckodriver.sh

celery -A tasks.celery.celery beat
