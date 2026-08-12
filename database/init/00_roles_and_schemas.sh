#!/usr/bin/env bash
set -Eeuo pipefail

required_variables=(
  POSTGRES_DB
  POSTGRES_USER
  QUERYGUARD_OWNER_PASSWORD
  QUERYGUARD_RUNTIME_PASSWORD
  QUERYGUARD_AUDIT_PASSWORD
)

for variable_name in "${required_variables[@]}"; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "Required initialization variable is empty: ${variable_name}" >&2
    exit 1
  fi
done

psql \
  --set=ON_ERROR_STOP=1 \
  --username "${POSTGRES_USER}" \
  --dbname "${POSTGRES_DB}" \
  --set=db_name="${POSTGRES_DB}" \
  --set=owner_password="${QUERYGUARD_OWNER_PASSWORD}" \
  --set=runtime_password="${QUERYGUARD_RUNTIME_PASSWORD}" \
  --set=audit_password="${QUERYGUARD_AUDIT_PASSWORD}" \
  --file=/opt/queryguard/database/roles.sql
