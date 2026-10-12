#!/bin/sh
# Container entrypoint: run migrations, collect static files, start gunicorn.
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn hms_enterprise.wsgi:application --bind 0.0.0.0:8000 --workers 3
