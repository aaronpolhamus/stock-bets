# db
# --
db-up:
	docker-compose up -d db

db-stop:
	docker-compose stop db

db-mysql:
	docker-compose exec db mysql -uroot -p

db-restart:
	make db-stop
	make db-up

db-reset:
	docker-compose exec api python -c "from backend.database.helpers import reset_db;reset_db()"

db-mock-data:
	make db-reset
	docker-compose exec api python -c "from backend.database.fixtures.mock_data import make_mock_data;make_mock_data()"

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

worker-restart:
	make worker-stop
	make worker-up

# celery scheduler
# ----------------
scheduler-logs:
	docker-compose logs -f scheduler

scheduler-up:
	docker-compose up -d scheduler
	make scheduler-logs

scheduler-build:
	docker-compose build scheduler

scheduler-stop:
	docker-compose stop scheduler

scheduler-restart:
	make scheduler-stop
	make scheduler-up

# flower
# ------
flower-up:
	docker-compose up -d flower

flower-stop:
	docker-compose stop flower

# redis
# -----
redis-mock-data:
	docker-compose exec api python -c "from backend.database.fixtures.mock_data import make_redis_mocks;make_redis_mocks()"

redis-clear:
	docker-compose exec api python -c "from backend.tasks.redis import rds;rds.flushall()"

# backend
# -------
backend-up:
	docker-compose up -d api

backend-build:
	docker-compose build backend

backend-test:
	rm -f backend/test_times.csv
	printf "test,time\n" >> backend/test_times.csv
	make worker-restart
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
up:
	make api-up
	./backend/docker/mock-data-runner.sh
	npm install --prefix frontend
	npm start --prefix frontend

down:
	docker-compose down

stop:
	docker-compose stop

destroy-everything: # (DANGER: this can be good hygiene/troubleshooting, but you'll need to rebuild your entire env)
	# Remove all containers
	make stop

	# remove all images
	docker rmi $(docker images -a -q) -f

	# prune all volumes
	docker volume prune -f

# e2e testing
# -----------
make e2e-test:
	docker-compose exec api python -m tests.e2e_scenario_test

# deployment
# ----------
ecr-login:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 781982251500.dkr.ecr.us-east-1.amazonaws.com

ecr-push:
	make backend-build
	docker tag backend:latest 781982251500.dkr.ecr.us-east-1.amazonaws.com/stockbets/backend:latest
	docker push 781982251500.dkr.ecr.us-east-1.amazonaws.com/stockbets/backend:latest

frontend-deploy:
	NODE_ENV=production npm run-script build --prefix frontend
	aws s3 sync frontend/build s3://app.stockbets.io --delete
	aws cloudfront create-invalidation --distribution-id E2PFNY4LEJWBAH --paths "/*"
