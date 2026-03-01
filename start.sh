#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting SimuTarget API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8001
