#!/usr/bin/env bash
# Fetch the backend's secrets from Infisical at startup using the dedicated,
# read-only Universal Auth identity delivered to the VM by CI. The credentials
# live in /opt/app/runtime.env on the host and are never baked into the image
# or Terraform state.
set -euo pipefail

project_id="$(jq -r '.infisical.backend_project_id' /app/config.json)"

if [[ -z "$project_id" || "$project_id" == "null" ]]; then
  echo "infisical_backend_project_id must be set in config.json" >&2
  exit 1
fi

if [[ -z "${INFISICAL_CLIENT_ID:-}" || -z "${INFISICAL_CLIENT_SECRET:-}" ]]; then
  echo "INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET must be supplied by runtime.env" >&2
  exit 1
fi

INFISICAL_TOKEN="$(infisical login --method=universal-auth \
  --client-id="$INFISICAL_CLIENT_ID" \
  --client-secret="$INFISICAL_CLIENT_SECRET" \
  --plain --silent)"
export INFISICAL_TOKEN

# Inject the backend secrets into the app process environment.
exec infisical run --projectId="$project_id" --env=prod --path=/backend -- "$@"
