#!/bin/bash

while ! python manage.py sqlflush > /dev/null 2>&1 ;do
    echo "Waiting for database..."
    sleep 1
done

echo "Prepare database migrations"
python manage.py makemigrations
echo "Apply database migrations"
python manage.py migrate


echo "Creating superuser"
python manage.py loaddata fixtures/superuser.json
echo "Loading some default tags and subjects"
python manage.py loaddata fixtures/task_tags_and_subjects.json


echo "Loading some site users"
python manage.py loaddata fixtures/users.json
echo "Loading some tasks"
python manage.py loaddata fixtures/tasks.json
echo "Loading some notifications"
python manage.py loaddata fixtures/notifications.json
echo "Loading some applications"
python manage.py loaddata fixtures/applications.json


echo "Runserver"
python manage.py runserver 0.0.0.0:8000
