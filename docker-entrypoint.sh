#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

cd webapp/db
python manager.py db upgrade # generate/update db schema

cd ../..
python wsgi.py # start the web application
