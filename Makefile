# db
# --
db-up:
	docker-compose up -d db

db-stop:
	docker-compose stop db

db-mysql:
	docker-compose exec db mysql -uroot -p

db-reset:
	docker-compose exec backend python -c "from backend.database.helpers import reset_db;reset_db()"

db-mock-data:
	docker-compose exec backend python -c "from backend.database.fixtures.mock_data import make_mock_data;make_mock_data()"

db-logs:
	docker-compose logs -f db

# celery worker
# -------------
worker-logs:
	docker-compose logs -f worker

worker-up:
	docker-compose up -d worker

worker-build:
	docker-compose build worker

worker-stop:
	docker-compose stop worker

worker-restart:
	make worker-stop
	make worker-build
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
	docker-compose exec backend python -c "from backend.database.fixtures.mock_data import make_redis_mocks;make_redis_mocks()"

# backend
# -------

backend-build:
	docker-compose build backend

backend-up:
	docker-compose up -d backend
	make worker-up

backend-logs:
	docker-compose logs -f backend

backend-bash:
	docker-compose exec backend bash

backend-python:
	docker-compose exec backend ipython

backend-stop:
	docker-compose stop backend

backend-test:
	docker-compose exec backend coverage run --source . -m unittest discover -v
	docker-compose exec backend coverage report

# frontend 
# --------

frontend-build:
	docker-compose build frontend

frontend-up:
	npm start --prefix frontend

# all containers
# --------------
up:
	make backend-up
	./backend/docker/mock-data-runner.sh
	npm install --prefix frontend
	npm start --prefix frontend

build:
	# leave the frontend out of this until we have deploy strategy sorted out...
	make backend-build

down:
	docker-compose down

stop:
	docker-compose stop

# deployment
# ----------
ecr-push:
	docker tag backend:latest 781982251500.dkr.ecr.us-west-1.amazonaws.com/stockbets/backend:latest
	docker push 781982251500.dkr.ecr.us-west-1.amazonaws.com/stockbets/backend:latest

