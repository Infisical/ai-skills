---
name: infisical-api
description: Interact with the Infisical REST API to manage secrets, projects, environments, machine identities, and more. Supports secret CRUD operations, machine identity authentication, pagination, and rate limiting on cloud deployments.
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

## Guiding Principles

1. **Always authenticate via machine identity Universal Auth first** — use the Universal Auth login endpoint to obtain a Bearer token before making other API calls
2. **Use /api/v4/secrets for secret operations** — v1/v2/v3 secret endpoints are deprecated
3. **Use /api/v1/projects, not /api/v1/workspace** — workspace endpoints are deprecated
4. **Pagination uses offset/limit** — default limit is 20, maximum is 100
5. **Region selection** — US region: us.infisical.com, EU region: eu.infisical.com
6. **Service tokens are deprecated** — use machine identities instead
7. **Rate limits apply to cloud only** — self-hosted deployments have no rate limits; free tier: 200 reads/min, pro tier: 350 reads/min

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

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev&offset=0&limit=20' \
  -H "Authorization: Bearer TOKEN"
```

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

- All requests must include `Content-Type: application/json` header
- Tokens expire after `expiresIn` seconds; implement refresh logic for long-running operations
- For self-hosted deployments, replace `us.infisical.com` with your custom domain
- Secret operations support multiple auth types (AWS, Azure, GCP, Kubernetes, OIDC, JWT, LDAP)
- Use `viewSecretValue=true` when listing secrets if you need to see actual values
- The `recursive` parameter on list secrets endpoint includes secrets in all subdirectories
