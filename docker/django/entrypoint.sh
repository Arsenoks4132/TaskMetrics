#!/bin/sh

set -e

echo "Waiting for database and applying migrations..."
until python manage.py migrate --noinput >/dev/null 2>&1; do
  sleep 2
done

python manage.py migrate --noinput

echo "Checking initial fixtures..."
if python manage.py shell -c "from Tasks.models import Category; import sys; sys.exit(0 if Category.objects.exists() else 1)"; then
  echo "Initial fixtures already loaded."
else
  echo "Loading initial fixtures..."
  python manage.py loaddata initial_fixture.json
fi

echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:8000 TaskAndTime.wsgi
