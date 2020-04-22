# DB
# --

db--up:
	docker-compose up db

# backend
# ------

backend--build:
	docker-compose build backend

backend--up:
	docker-compose up backend

# frontend 
# --------

frontend--build:
	docker-compose build frontend

frontend--up:
	docker-compose up frontend

# All containers
# --------------

build:
	docker-compose build

up:
	docker-compose up

stop:
	docker-compose stop

down:
	docker-compose down
