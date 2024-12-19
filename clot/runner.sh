#!/bin/bash

black ../.

pip freeze > ../requirements.txt

python manage.py makemigrations

sleep 1

python manage.py migrate

sleep 1

python manage.py runserver

