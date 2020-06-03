#!/usr/bin/env bash
until docker-compose exec backend nc -z -v -w30 $DB_HOST 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

make db-reset
make db-mock-data
make redis-mock-data
