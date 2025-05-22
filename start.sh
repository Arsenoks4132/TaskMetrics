#!/bin/bash

set -e

echo "📦 Билдим и запускаем docker-compose..."
docker compose up -d --build

echo "⏳ Ждём готовности базы данных..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' $(docker compose ps -q postgres_db))" == "healthy" ]; do
  echo "Postgres не готов, подождём..."
  sleep 2
done

echo "🔁 Применяем миграции..."
docker compose exec django_backend python manage.py migrate

echo "💾 Загружаем фикстуры..."
docker compose exec django_backend python manage.py loaddata initial_fixture.json

echo "✅ Всё готово!"
