#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  # wait for a second before checking again
  sleep 1
done

cd db
python manager.py db upgrade # generate/update db schema

cd ../webapp
python app.py # start the web application
