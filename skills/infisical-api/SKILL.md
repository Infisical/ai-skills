---
name: infisical-api
description: Interact with the Infisical REST API to manage secrets, projects, environments, machine identities, and more. Supports secret CRUD operations, machine identity authentication, pagination, and rate limiting on cloud deployments. Not for the CLI/SDKs (infisical-setup), KMS crypto endpoints (infisical-kms), certificate endpoints (infisical-pki), or human SSO login (infisical-sso).
triggers:
  - infisical API
  - REST endpoint
  - API authentication
  - bearer token
  - list secrets API
  - create secret API
  - get secret
  - update secret
  - delete secret
  - machine identity
  - universal auth
  - project endpoints
  - secret operations
---

# Infisical API Skill

This skill provides guidance for working with the Infisical REST API. Use it when you need to:
- Authenticate via machine identity Universal Auth
- List, get, create, update, or delete secrets
- Manage projects, environments, and members
- Work with machine identities and identity auth methods
- Handle pagination and understand rate limits
- Choose the correct API version and region

## Not this skill

| If the user wants... | Use |
|----------------------|-----|
| The CLI, an SDK, or a platform integration | `infisical-setup` |
| Terraform/HCL | `infisical-terraform` |
| **Human** login via SAML/OIDC/LDAP | `infisical-sso` |
| Roles, permissions, and approval policies | `infisical-access-control` |
| The KMS encrypt/decrypt/sign endpoints | `infisical-kms` |
| Certificate endpoints | `infisical-pki` |
| Secret sync / rotation / App Connection endpoints | the matching product skill |

This skill covers the core secrets, projects, and identities API. Product-specific endpoints are
documented in their own skills, where the surrounding concepts live.

## Guiding Principles

1. **Always authenticate via machine identity Universal Auth first** — use the Universal Auth login endpoint to obtain a Bearer token before making other API calls
2. **Use /api/v4/secrets for secret operations** — v1/v2/v3 secret endpoints are deprecated
3. **Use /api/v1/projects, not /api/v1/workspace** — workspace endpoints are deprecated
4. **`/api/v4/secrets` is not paginated** — it returns every secret at the requested path in one response and ignores `offset`/`limit`. Scope results with `secretPath`, `recursive`, `tagSlugs`, or `metadataFilter` instead. Pagination exists on other collection endpoints (identities, memberships, certificates), which return `{ <resource>: [...], totalCount: n }`
5. **Region selection** — US region: us.infisical.com, EU region: eu.infisical.com
6. **Service tokens are deprecated** — use machine identities instead
7. **Rate limits apply to self-hosted too** — they are not cloud-only. Instance defaults are 60 reads/min, 200 writes/min, 60 secrets-ops/min, 60 auth/min per IP; self-hosted admins can change them, and cloud limits vary by plan. On a 429, honor the `retry-after` header (seconds remaining, not a timestamp)
8. **Batch over loop** — use `POST/PATCH/DELETE /api/v4/secrets/batch` rather than per-secret calls; batch delete takes `secrets: [{ secretKey }]`

## Reference Files

- [Authentication](./references/authentication.md) — Universal Auth login, auth endpoints, token patterns, deprecated service tokens
- [Secrets Endpoints](./references/secrets-endpoints.md) — CRUD operations on secrets using /api/v4/secrets
- [Projects and Identities](./references/projects-and-identities.md) — project management, environments, members, identities, groups, folders
- [Pagination and Rate Limits](./references/pagination-and-rate-limits.md) — offset/limit pagination, cloud rate limits, content-type requirements

## Quick Start

### 1. Authenticate with Universal Auth

```bash
curl -X POST https://us.infisical.com/api/v1/auth/universal-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

Response:
```json
{
  "accessToken": "eyJ...",
  "expiresIn": 3600,
  "accessTokenMaxTTL": 86400,
  "tokenType": "Bearer"
}
```

### 2. Use the Token for Subsequent Requests

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev' \
  -H "Authorization: Bearer eyJ..."
```

## Common Workflows

### List All Secrets in a Project

Returns every secret at the path — there is no pagination on this endpoint.

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev' \
  -H "Authorization: Bearer TOKEN"
```

Add `recursive=true` to include subfolders:

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev&secretPath=/&recursive=true' \
  -H "Authorization: Bearer TOKEN"
```

Response is `{ "secrets": [...], "imports": [...] }` — no `total`, `offset`, or `limit` keys.

### Create a New Secret

```bash
curl -X POST 'https://us.infisical.com/api/v4/secrets/MY_SECRET' \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "PROJECT_ID",
    "environment": "dev",
    "secretPath": "/",
    "secretValue": "super-secret-value",
    "type": "shared"
  }'
```

### Get a Specific Secret

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets/MY_SECRET?projectId=PROJECT_ID&environment=dev&secretPath=/' \
  -H "Authorization: Bearer TOKEN"
```

### Update a Secret

```bash
curl -X PATCH 'https://us.infisical.com/api/v4/secrets/MY_SECRET' \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "PROJECT_ID",
    "environment": "dev",
    "secretPath": "/",
    "secretValue": "new-value"
  }'
```

### Delete a Secret

```bash
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/MY_SECRET?projectId=PROJECT_ID&environment=dev&secretPath=/' \
  -H "Authorization: Bearer TOKEN"
```

## Important Notes

- Include `Content-Type: application/json` on any request that carries a JSON body
- Tokens expire after `expiresIn` seconds; implement refresh logic for long-running operations
- For self-hosted deployments, replace `us.infisical.com` with your custom domain
- Secret operations support all 13 machine identity auth methods (Universal, Token, Kubernetes, GCP, AliCloud, AWS, Azure, TLS Cert, OCI, OIDC, JWT, LDAP, SPIFFE)
- `viewSecretValue` defaults to `true`; set it to `false` when you only need key names
- The `recursive` parameter on list secrets includes secrets in all subdirectories
- Beyond CRUD, `/api/v4/secrets` also exposes `/move`, `/duplicate`, `/batch` (POST, PATCH, DELETE), `/id/:secretId`, and secret-reference tree endpoints
