#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

# setup the chrome driver that we will use for webscraping
curl -LO $CHROMIUM_DRIVER_LOCATION
unzip chromedriver_linux64.zip

# clean up compressed zip files
rm -rf *zip

celery -A tasks.celery.celery worker --concurrency=20 --loglevel=info
