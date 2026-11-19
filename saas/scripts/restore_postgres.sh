#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to the target PostgreSQL connection string}"
backup_file="${1:?Pass a trusted backup .dump file}"
if [[ ! -f "$backup_file" ]]; then
  echo "Backup file not found: $backup_file" >&2
  exit 2
fi
echo "This replaces tables in the target database. Target: ${DATABASE_URL%%@*}@…"
read -r -p 'Type RESTORE to continue: ' confirmation
if [[ "$confirmation" != "RESTORE" ]]; then
  echo "Restore cancelled."
  exit 1
fi
pg_restore --clean --if-exists --no-owner --no-acl --dbname "$DATABASE_URL" "$backup_file"
echo "Restore completed from: $backup_file"
