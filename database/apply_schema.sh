#!/usr/bin/env bash
set -Eeuo pipefail

docker compose exec -T postgres bash -c '
    set -Eeuo pipefail
    PGPASSWORD="${QUERYGUARD_OWNER_PASSWORD}" psql \
        --host=127.0.0.1 \
        --username=queryguard_owner \
        --dbname="${POSTGRES_DB}" \
        --set=ON_ERROR_STOP=1 \
        --file=/opt/queryguard/database/schema.sql
'
