#!/usr/bin/env bash
set -Eeuo pipefail

PGPASSWORD="${QUERYGUARD_OWNER_PASSWORD}" psql \
  --username=queryguard_owner \
  --dbname="${POSTGRES_DB}" \
  --set=ON_ERROR_STOP=1 \
  --file=/opt/queryguard/database/schema.sql
