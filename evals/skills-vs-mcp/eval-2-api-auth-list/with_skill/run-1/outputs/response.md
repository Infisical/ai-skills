# Infisical API: Machine Identity Authentication & Secret Listing

## Overview
This guide shows how to authenticate with Infisical's REST API using a machine identity (Universal Auth) and then list all secrets in a project's dev environment.

## Step 1: Authenticate with Universal Auth

First, obtain an access token using your machine identity credentials:

```bash
curl -X POST https://us.infisical.com/api/v1/auth/universal-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**Important Notes:**
- Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your actual machine identity credentials
- The access token expires after `expiresIn` seconds (3600 = 1 hour)
- For EU region, use `https://eu.infisical.com` instead of `https://us.infisical.com`
- Machine identities are the recommended authentication method (service tokens are deprecated)

## Step 2: List All Secrets in Dev Environment

Use the access token to list all secrets in your project's dev environment:

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=YOUR_PROJECT_ID&environment=dev&viewSecretValue=true' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "secrets": [
    {
      "id": "secret-id-1",
      "key": "DATABASE_URL",
      "value": "postgresql://user:pass@localhost:5432/db",
      "environment": "dev",
      "createdAt": "2026-04-17T10:00:00Z",
      "updatedAt": "2026-04-17T10:00:00Z"
    },
    {
      "id": "secret-id-2",
      "key": "API_KEY",
      "value": "sk_dev_1234567890abcdef",
      "environment": "dev",
      "createdAt": "2026-04-17T11:30:00Z",
      "updatedAt": "2026-04-17T11:30:00Z"
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 20,
    "total": 2
  }
}
```

**Parameters:**
- `projectId` — Your project ID (required)
- `environment` — Environment name (e.g., dev, staging, prod)
- `viewSecretValue=true` — Include actual secret values in response
- `offset` — Pagination offset (default: 0)
- `limit` — Number of results per page (default: 20, maximum: 100)

## Complete Example Script

Here's a complete bash script combining both steps:

```bash
#!/bin/bash

# Configuration
CLIENT_ID="YOUR_CLIENT_ID"
CLIENT_SECRET="YOUR_CLIENT_SECRET"
PROJECT_ID="YOUR_PROJECT_ID"
REGION="us"  # or "eu" for EU region

# Step 1: Authenticate
echo "Authenticating with Infisical..."
AUTH_RESPONSE=$(curl -s -X POST "https://${REGION}.infisical.com/api/v1/auth/universal-auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"${CLIENT_ID}\",
    \"clientSecret\": \"${CLIENT_SECRET}\"
  }")

ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.accessToken')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
  echo "Authentication failed!"
  echo "$AUTH_RESPONSE"
  exit 1
fi

echo "✓ Authentication successful"
echo "Token expires in: $(echo "$AUTH_RESPONSE" | jq -r '.expiresIn') seconds"

# Step 2: List secrets
echo ""
echo "Fetching secrets from dev environment..."
SECRETS_RESPONSE=$(curl -s -X GET "https://${REGION}.infisical.com/api/v4/secrets?projectId=${PROJECT_ID}&environment=dev&viewSecretValue=true" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

echo "$SECRETS_RESPONSE" | jq '.'
```

## Key Takeaways

✓ **Use `/api/v4/secrets`** — v1/v2/v3 secret endpoints are deprecated
✓ **Machine Identity + Universal Auth** — Recommended authentication method
✓ **Include `Content-Type: application/json`** — Required header for all requests
✓ **Use `viewSecretValue=true`** — To see actual secret values
✓ **Region selection** — us.infisical.com (US) or eu.infisical.com (EU)
✓ **Pagination** — Use offset/limit for large secret sets (default limit: 20, max: 100)
✓ **Token expiration** — Tokens expire after 1 hour; implement refresh logic for long-running processes
