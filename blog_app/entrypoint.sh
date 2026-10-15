#!/bin/sh
set -e

echo "Waiting for the database to be ready..."
until python -c "
import asyncio, os, asyncpg
async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
  echo "  database not ready yet, retrying in 1s..."
  sleep 1
done
echo "Database is ready."

echo "Running migrations..."
alembic upgrade head

echo "Starting the server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
