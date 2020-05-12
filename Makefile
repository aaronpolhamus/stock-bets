# db
# --

db-build:
	docker-compose build db

db-up:
	docker-compose up -d db

db-mysql:
	docker-compose exec db mysql -uroot -p

db-reset:
	docker-compose exec backend python -c "from backend.database.fixtures.mock_data import make_mock_data;make_mock_data()"

# backend
# ------

backend-build:
	docker-compose build backend

backend-up:
	docker-compose up -d backend

backend-logs:
	docker-compose logs -f backend

backend-bash:
	docker-compose exec backend bash

backend-test:
	docker-compose exec backend python -m unittest discover tests

# frontend 
# --------

frontend-build:
	docker-compose build frontend

frontend-up:
	docker run -p 80:80 frontend

# all containers
# --------------
down:
	docker-compose down

stop:
	docker-compose stop
