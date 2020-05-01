# DB
# --

db--up:
	docker-compose up db

db--test_populate:
	# insert commandd to populate test data here

# backend
# ------

backend--build:
	docker-compose build backend

backend--up:
	docker-compose up backend

backend--test:
	docker-compose up backend
	make db--test_populate

# frontend 
# --------

frontend--build:
	docker-compose build frontend

frontend--up:
	docker run -p 80:80 frontend

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
