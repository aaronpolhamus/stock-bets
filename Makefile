# DB
# --

db--build:
	docker-compose build db

db--up:
	docker-compose up db

db--upgrade:
	docker exec -it backend flask db upgrade

# Backend
# -------

backend--build:
	docker-compose build backend

backend--up:
	docker-compose up backend

# Application
# -----------

build:
	docker-compose build

up:
	docker-compose up

