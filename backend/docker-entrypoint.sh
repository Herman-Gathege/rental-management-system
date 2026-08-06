#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until pg_isready \
    -h postgres \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB"
do
    sleep 2
done

echo "PostgreSQL is ready."

echo "Running database migrations..."
alembic upgrade head

echo "Seeding roles..."
python -m app.db.seed_roles

echo "Starting FastAPI..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers