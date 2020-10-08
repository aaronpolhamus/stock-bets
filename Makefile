# db
# --
db-up:
	docker-compose up -d db

db-stop:
	docker-compose stop db

db-mysql:
	docker-compose exec db mysql -uroot

db-await:
	./backend/docker/await-db.sh

db-reset: s3-reset
	docker-compose exec api python -c "from backend.database.helpers import reset_db;reset_db()"

db-mock-data: db-reset
	rm -f backend/mockdata.sql
	docker-compose exec api python -m database.fixtures.make_historical_price_data
	docker-compose exec api python -c "from backend.database.fixtures.mock_data import make_db_mocks;make_db_mocks()"
	docker-compose exec db mysqldump -uroot main > backend/mockdata.sql

s3-reset:
	rm -rf .localstack/data/*.json

s3-buckets: db-await
	docker-compose exec api aws --endpoint-url=http://localstack:4572 s3 mb s3://stockbets-public
	docker-compose exec api aws --endpoint-url=http://localstack:4572 s3 mb s3://stockbets-private
	docker-compose exec api aws --endpoint-url=http://localstack:4572 s3api put-bucket-acl --bucket stockbets-public --acl public-read

s3-mock-data: s3-buckets
	docker-compose exec api python -c "from backend.database.fixtures.mock_data import make_s3_mocks;make_s3_mocks()"

db-logs:
	docker-compose logs -f db

# celery worker
# -------------
worker-logs:
	docker-compose logs -f worker

worker-up:
	docker-compose up -d worker

worker-stop:
	docker-compose stop worker

worker-restart: worker-stop worker-up

# celery scheduler
# ----------------
scheduler-logs:
	docker-compose logs -f scheduler

scheduler-up:
	docker-compose up -d scheduler

scheduler-build:
	docker-compose build scheduler

scheduler-stop:
	docker-compose stop scheduler

scheduler-restart: scheduler-stop scheduler-up

# flower
# ------
flower-up:
	docker-compose up -d flower

flower-stop:
	docker-compose stop flower

# redis
# -----
redis-mock-data: redis-clear
	docker-compose exec api python -c "from backend.database.fixtures.mock_data import make_redis_mocks;make_redis_mocks()"

redis-clear:
	docker-compose exec api python -c "from backend.tasks.redis import rds;rds.flushall()"

# airflow
# -----------------
airflow-up:
	docker-compose up -d airflow

airflow-start:
	docker-compose start airflow

airflow-stop:
	docker-compose stop airflow

airflow-clear-logs:
	rm -rf ./backend/airflow/logs

airflow-restart: airflow-stop airflow-start

airflow-logs:
	docker-compose logs -f airflow

airflow-bash:
	docker-compose exec airflow bash

# backend
# -------
backend-up:
	docker-compose up -d api

backend-build: airflow-clear-logs s3-reset
	docker-compose build backend

backend-test: api-up s3-buckets db-mock-data worker-restart airflow-restart
	rm -f backend/test_times.csv
	printf "test,time\n" >> backend/test_times.csv
	docker-compose exec api coverage run --source . -m unittest discover -v
	docker-compose exec api coverage report

# API
# ---
api-up:
	docker-compose up -d api

api-logs:
	docker-compose logs -f api

api-bash:
	docker-compose exec api bash

api-python:
	docker-compose exec api ipython

api-stop:
	docker-compose stop api

# all containers
# --------------
up: api-up db-await mock-data
	npm install --prefix frontend
	npm start --prefix frontend

down:
	docker-compose down

stop:
	docker-compose stop

destroy-everything: stop # (DANGER: this can be good hygiene/troubleshooting, but you'll need to rebuild your entire env)
	# remove all images
	docker rmi $(docker images -a -q) -f

	# prune all volumes
	docker volume prune -f

aggressive-stop:
	docker rm -f $$(docker ps -a -q)

remove-dangling:
	# good hygiene to free up some hard drive every now and again
	docker rmi $(docker images --filter "dangling=true" -q --no-trunc)


# e2e testing
# -----------
mock-data: db-mock-data s3-mock-data redis-mock-data

e2e-test:
	docker-compose exec api python -m tests.e2e_scenario_test

# deployment
# ----------
ecr-login:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 781982251500.dkr.ecr.us-east-1.amazonaws.com

ecr-push: backend-build
	docker tag backend:latest 781982251500.dkr.ecr.us-east-1.amazonaws.com/stockbets/backend:latest
	docker push 781982251500.dkr.ecr.us-east-1.amazonaws.com/stockbets/backend:latest

frontend-deploy:
	NODE_ENV=production npm run-script build --prefix frontend
	aws s3 sync frontend/build s3://app.stockbets.io --delete
	aws cloudfront create-invalidation --distribution-id E2PFNY4LEJWBAH --paths "/*"

# local debugging helpers
# ------------------------
jupyter:
	docker-compose exec api jupyter notebook --ip=0.0.0.0 --allow-root --port 8050