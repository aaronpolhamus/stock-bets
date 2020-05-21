#!/usr/bin/env bash
until nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

# construct the data model
flask db upgrade

# update timestamps on historical price mocks
python -m database.fixtures.make_historical_price_data

# start the web application
python wsgi.py
