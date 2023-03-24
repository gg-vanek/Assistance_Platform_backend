#!/bin/bash

while ! python manage.py sqlflush > /dev/null 2>&1 ;do
    echo "Waiting for database..."
    sleep 1
done

echo "Prepare database migrations"
python manage.py makemigrations

echo "Apply database migrations"
python manage.py migrate

echo "Loading some default data"
python manage.py loaddata fixtures/some_data.json

echo "Runserver"
python manage.py runserver 0.0.0.0:8000
