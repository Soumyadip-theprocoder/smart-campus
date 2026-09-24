#!/bin/bash
echo "Starting background worker..."
python manage.py qcluster &
echo "Seeding data..."
python seed_data.py
echo "Starting web server..."
gunicorn config.wsgi:application
