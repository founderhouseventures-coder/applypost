#!/usr/bin/env bash
set -euo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$script_dir/../.." && pwd)"
compose_file="$script_dir/compose.yaml"
backup_dir="${BACKUP_DIR:-$app_dir/backups}"
backup_file="$backup_dir/jobmail-$(date -u +%Y%m%dT%H%M%SZ).dump"
backup_tmp="$backup_file.tmp"

mkdir -p "$backup_dir"
docker compose --project-directory "$app_dir" -f "$compose_file" \
  exec -T db sh -ec 'pg_dump --format=custom --no-owner --no-acl -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "$backup_tmp"
test -s "$backup_tmp"
mv "$backup_tmp" "$backup_file"
chmod 600 "$backup_file"
find "$backup_dir" -type f -name 'jobmail-*.dump' -mtime +14 -delete
echo "Created local backup: $backup_file"
