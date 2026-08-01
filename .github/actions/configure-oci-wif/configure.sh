#!/usr/bin/env bash
set -euo pipefail

: "${OCI_WIF_IDENTITY_DOMAIN_URL:?Missing OCI Identity Domain URL}"
: "${OCI_WIF_TENANCY_OCID:?Missing OCI tenancy OCID}"
: "${OCI_WIF_SERVICE_USER_OCID:?Missing OCI WIF service-user OCID}"
: "${OCI_WIF_REGION:?Missing OCI region}"
: "${OCI_WIF_AUDIENCE:?Missing OCI WIF audience}"
: "${oci_github_client_id:?Missing /deploy oci_github_client_id}"
: "${oci_github_client_secret:?Missing /deploy oci_github_client_secret}"
: "${ACTIONS_ID_TOKEN_REQUEST_URL:?GitHub OIDC is unavailable; grant id-token: write}"
: "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:?GitHub OIDC is unavailable; grant id-token: write}"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

# OCI binds the exchanged security token to this ephemeral key. It is neither
# uploaded nor reused; both it and the token disappear when this job ends.
openssl genrsa -out "$work_dir/private_key.pem" 2048 >/dev/null 2>&1
# OCI's token-exchange endpoint expects only the Base64 body—not PEM markers
# or line breaks—even though the key is generated as a PEM file.
public_key="$(openssl rsa -in "$work_dir/private_key.pem" -pubout 2>/dev/null | sed '1d;$d' | tr -d '\n\r')"

github_jwt="$({
  curl --fail-with-body --silent --show-error \
    -H "Authorization: Bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
    -H 'Accept: application/json; api-version=2.0' \
    "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=${OCI_WIF_AUDIENCE}"
} | jq -er '.value')"

token_response_file="$work_dir/token-response.json"
token_status="$(curl --silent --show-error --output "$token_response_file" --write-out '%{http_code}' \
  --user "${oci_github_client_id}:${oci_github_client_secret}" \
  --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \
  --data-urlencode 'requested_token_type=urn:oci:token-type:oci-upst' \
  --data-urlencode "public_key=${public_key}" \
  --data-urlencode "subject_token=${github_jwt}" \
  --data-urlencode 'subject_token_type=jwt' \
  "${OCI_WIF_IDENTITY_DOMAIN_URL%/}/oauth2/v1/token")"
if [[ "$token_status" != 2* ]]; then
  jq -r '"OCI token exchange failed: " + (.error_description // .error // "HTTP " + $status)' \
    --arg status "$token_status" "$token_response_file" >&2
  exit 1
fi
token_response="$(<"$token_response_file")"
security_token="$(jq -er '.token' <<<"$token_response")"

config_dir="$RUNNER_TEMP/oci-wif"
mkdir -p "$config_dir"
chmod 700 "$config_dir"
cp "$work_dir/private_key.pem" "$config_dir/private_key.pem"
printf '%s' "$security_token" > "$config_dir/security_token"
chmod 600 "$config_dir/private_key.pem" "$config_dir/security_token"

cat > "$config_dir/config" <<EOF
[GITHUB_WIF]
user=${OCI_WIF_SERVICE_USER_OCID}
fingerprint=00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00
key_file=${config_dir}/private_key.pem
tenancy=${OCI_WIF_TENANCY_OCID}
region=${OCI_WIF_REGION}
security_token_file=${config_dir}/security_token
EOF
chmod 600 "$config_dir/config"

# The OCI Terraform provider resolves its config from the standard OCI CLI
# location. Keep the sensitive key and token in RUNNER_TEMP, and install only
# this short-lived config file into the ephemeral runner home directory.
mkdir -p "$HOME/.oci"
chmod 700 "$HOME/.oci"
cp "$config_dir/config" "$HOME/.oci/config"
chmod 600 "$HOME/.oci/config"

{
  echo "OCI_CONFIG_FILE=$config_dir/config"
  echo "OCI_CLI_CONFIG_FILE=$config_dir/config"
  echo 'OCI_CONFIG_FILE_PROFILE=GITHUB_WIF'
  echo 'OCI_AUTH=SecurityToken'
} >> "$GITHUB_ENV"

echo 'Configured short-lived OCI WIF credentials.'
