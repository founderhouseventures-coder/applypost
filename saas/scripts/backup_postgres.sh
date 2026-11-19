#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to the PostgreSQL connection string}"
backup_dir="${BACKUP_DIR:-./backups}"
mkdir -p "$backup_dir"
backup_file="$backup_dir/jobmail-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --no-owner --no-acl "$DATABASE_URL" --file "$backup_file"
echo "Backup created: $backup_file"
