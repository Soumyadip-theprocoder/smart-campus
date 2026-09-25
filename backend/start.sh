#!/bin/bash
echo "Starting background worker..."
python manage.py qcluster &
echo "Starting web server..."
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
