#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$script_dir/../.." && pwd)"
compose_file="$script_dir/compose.yaml"

if [[ ! -f "$app_dir/.env" ]]; then
  echo "Missing $app_dir/.env; copy .env.oci.example and set its private values." >&2
  exit 1
fi

docker compose --project-directory "$app_dir" -f "$compose_file" config --quiet
docker compose --project-directory "$app_dir" -f "$compose_file" up -d --build --remove-orphans
docker compose --project-directory "$app_dir" -f "$compose_file" ps
