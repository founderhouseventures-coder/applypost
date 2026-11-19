#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$script_dir/../.." && pwd)"
compose_file="$script_dir/compose.yaml"
backup_file="${1:?Usage: restore.sh /path/to/jobmail-backup.dump}"

if [[ ! -f "$backup_file" ]]; then
  echo "Backup file not found: $backup_file" >&2
  exit 2
fi

echo "This replaces the JobMail database with $backup_file."
read -r -p 'Type RESTORE JOBMAIL to continue: ' confirmation
if [[ "$confirmation" != "RESTORE JOBMAIL" ]]; then
  echo "Restore cancelled."
  exit 1
fi

docker compose --project-directory "$app_dir" -f "$compose_file" \
  exec -T db pg_restore --clean --if-exists --no-owner --no-acl \
    -U jobmail -d jobmail < "$backup_file"
echo "Restore completed. Verify /health/ and a synthetic account before serving users."
