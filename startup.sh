#!/bin/bash
nohup celery worker -A itmsp >> ./logs/celery.log 2>&1 & && nohup python manage.py runserver 0.0.0.0:80 >> ./logs/build.log 2>&1 &