#!/usr/bin/env bash
until docker-compose exec api nc -z -v -w30 $DB_HOST $DB_PORT
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done

make db-mock-data
make redis-mock-data

# update timestamps on historical price mocks
docker-compose exec api python -m database.fixtures.make_historical_price_data