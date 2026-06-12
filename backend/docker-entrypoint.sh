#!/usr/bin/env bash
# Fetch the backend's secrets from Infisical at startup using this VM's GCE
# instance identity (no static credentials are stored on the VM or in the
# image), then exec the app with those secrets injected into its environment.
set -euo pipefail

CONFIG_FILE=/app/config.env

read_config() {
  grep -E "^$1=" "$CONFIG_FILE" | cut -d= -f2- | tr -d '"[:space:]'
}

project_id="$(read_config infisical_project_id)"
identity_id="$(read_config infisical_backend_identity_id)"

if [[ -z "$project_id" || -z "$identity_id" ]]; then
  echo "infisical_project_id and infisical_backend_identity_id must be set in config.env" >&2
  exit 1
fi

# Authenticate via the GCP ID Token (GCE instance identity) method. The CLI
# fetches the instance identity token from the metadata server and exchanges it
# for a short-lived Infisical access token.
INFISICAL_TOKEN="$(infisical login --method=gcp-id-token \
  --machine-identity-id="$identity_id" --plain --silent)"
export INFISICAL_TOKEN

# Inject the backend secrets into the app process environment.
exec infisical run --projectId="$project_id" --env=prod --path=/backend -- "$@"
