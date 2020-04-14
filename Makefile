# DB
# --

db--up:
	docker-compose up db

# Webapp
# ------

webapp--build:
	docker-compose build webapp

webapp--up:
	docker-compose up webapp

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
