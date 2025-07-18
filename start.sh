#!/bin/bash

reset

docker compose down --volumes --remove-orphans

docker system prune --force

docker compose build --progress plain

docker compose up --detach

docker compose exec app python3 manage.py makemigrations

docker compose exec app python3 manage.py migrate

# you may need to run the following command only once during the first run:
#&& docker compose exec app python3 manage.py createsuperuser \
docker compose logs --tail 100 --follow --timestamps
