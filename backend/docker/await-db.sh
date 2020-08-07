#!/usr/bin/env bash
until docker-compose exec api nc -z -v -w30 db 3306
do
  echo "Waiting a second until the database is receiving connections..."
  sleep 1
done
