#!/usr/bin/env bash
set -euo pipefail

: "${OCI_WIF_IDENTITY_DOMAIN_URL:?Missing OCI Identity Domain URL}"
: "${OCI_WIF_GITHUB_REPOSITORY:?Missing GitHub repository}"
: "${OCI_WIF_GITHUB_AUDIENCE:?Missing GitHub OIDC audience}"
: "${oci_github_client_id:?Missing /deploy oci_github_client_id}"
: "${oci_github_client_secret:?Missing /deploy oci_github_client_secret}"

domain_url="${OCI_WIF_IDENTITY_DOMAIN_URL%/}"
service_username="decent-visualizer-github-wif"
group_name="decent-visualizer-tofu"
trust_name="decent-visualizer-github-actions"
subject="repo:${OCI_WIF_GITHUB_REPOSITORY}:ref:refs/heads/main"

admin_token="$(curl --fail-with-body --silent --show-error \
  --user "${oci_github_client_id}:${oci_github_client_secret}" \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'scope=urn:opc:idm:__myscopes__' \
  "${domain_url}/oauth2/v1/token" | jq -er '.access_token')"

api() {
  curl --fail-with-body --silent --show-error \
    -H "Authorization: Bearer ${admin_token}" \
    -H 'Content-Type: application/json' \
    "$@"
}

service_user_id="$(api --get --data-urlencode "filter=userName eq \"${service_username}\"" \
  "${domain_url}/admin/v1/Users" | jq -r '.Resources[0].id // empty')"
if [[ -z "$service_user_id" ]]; then
  service_user_id="$(api --request POST "${domain_url}/admin/v1/Users" \
    --data @- <<EOF | jq -er '.id'
{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"${service_username}","urn:ietf:params:scim:schemas:oracle:idcs:extension:user:User":{"serviceUser":true}}
EOF
  )"
fi

group_id="$(api --get --data-urlencode "filter=displayName eq \"${group_name}\"" \
  "${domain_url}/admin/v1/Groups" | jq -r '.Resources[0].id // empty')"
if [[ -z "$group_id" ]]; then
  group_id="$(api --request POST "${domain_url}/admin/v1/Groups" --data @- <<EOF | jq -er '.id'
{"schemas":["urn:ietf:params:scim:schemas:core:2.0:Group"],"displayName":"${group_name}","members":[{"value":"${service_user_id}"}]}
EOF
  )"
fi

# A group might have existed from a partial bootstrap run. Ensure that the
# federated service user is a member before relying on tenancy IAM policies.
if ! api --get "${domain_url}/admin/v1/Groups/${group_id}" | jq -e --arg id "$service_user_id" \
  'any(.members[]?; .value == $id)' >/dev/null; then
  api --request PATCH "${domain_url}/admin/v1/Groups/${group_id}" --data @- <<EOF >/dev/null
{"schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],"Operations":[{"op":"add","path":"members","value":[{"value":"${service_user_id}"}]}]}
EOF
fi

trust_id="$(api --get --data-urlencode "filter=name eq \"${trust_name}\"" \
  "${domain_url}/admin/v1/IdentityPropagationTrusts" | jq -r '.Resources[0].id // empty')"
if [[ -z "$trust_id" ]]; then
  trust_id="$(api --request POST "${domain_url}/admin/v1/IdentityPropagationTrusts" --data @- <<EOF | jq -er '.id'
{"schemas":["urn:ietf:params:scim:schemas:oracle:idcs:IdentityPropagationTrust"],"name":"${trust_name}","description":"GitHub Actions OIDC trust for OpenTofu","type":"JWT","active":true,"issuer":"https://token.actions.githubusercontent.com","publicKeyEndpoint":"https://token.actions.githubusercontent.com/.well-known/jwks","oauthClients":["${oci_github_client_id}"],"clientClaimName":"aud","clientClaimValues":["${OCI_WIF_GITHUB_AUDIENCE}"],"allowImpersonation":true,"impersonationServiceUsers":[{"rule":"sub eq ${subject}","value":"${service_user_id}"}],"subjectType":"User"}
EOF
  )"
fi

{
  echo "### OCI GitHub WIF bootstrap complete"
  echo
  echo "Service user OCID: \`${service_user_id}\`"
  echo "Identity-domain group: \`${group_name}\`"
  echo "Trust ID: \`${trust_id}\`"
  echo
  echo "Next, create the tenancy IAM policy granting this group permission to manage dynamic groups and policies."
} >> "$GITHUB_STEP_SUMMARY"

echo "OCI_WIF_SERVICE_USER_OCID=${service_user_id}" >> "$GITHUB_ENV"
echo "::notice title=OCI WIF service user OCID::${service_user_id}"
echo "OCI WIF service user OCID: ${service_user_id}"
