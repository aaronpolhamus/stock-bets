# DB
# --

db--build:
	docker-compose build db

db--up:
	docker-compose up db

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