#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  sleep 2
done

echo "Starting PostgreSQL backup loop..."
while true; do
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  FILE="/backups/backup_${TIMESTAMP}.sql.gz"
  echo "Creating backup: $FILE"
  pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"
  echo "Backup completed successfully."

  # Retain only last 7 days
  find /backups -name "backup_*.sql.gz" -type f -mtime +7 -delete

  sleep 86400
done
