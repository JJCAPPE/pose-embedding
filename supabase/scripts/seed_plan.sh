#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
plan_path="${1:-${repo_root}/plan/research-plan.v1.json}"
import_path="${repo_root}/supabase/scripts/import_plan.sql"

: "${POSE_EMBED_DB_URL:?Set POSE_EMBED_DB_URL to the target Postgres connection URL.}"

for command_name in jq psql; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Required command not found: ${command_name}" >&2
    exit 2
  fi
done

if [[ ! -f "${plan_path}" ]]; then
  echo "Plan file not found: ${plan_path}" >&2
  exit 2
fi

plan_json="$(jq -ce '
  select(.schemaVersion == "1.0.0")
  | select(.project.slug | type == "string")
  | select(.weeks | length == 14)
' "${plan_path}")"

psql_args=(
  --no-psqlrc
  --set ON_ERROR_STOP=1
  --set "plan_json=${plan_json}"
  --set "owner_email=${POSE_EMBED_OWNER_EMAIL:-}"
)

psql "${POSE_EMBED_DB_URL}" "${psql_args[@]}" --file "${import_path}"
