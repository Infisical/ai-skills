# Infisical REST API: Machine Identity Authentication & Secret Listing

## Overview

Infisical supports machine identity authentication via JWT tokens generated from client credentials. This guide shows how to authenticate and list secrets using curl.

## Step 1: Authenticate with Machine Identity

### Generate Access Token

Use your machine identity credentials to obtain an access token:

```bash
curl -X POST https://app.infisical.com/api/v1/auth/machine-identity/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

**Response** (success):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}
```

Save the `accessToken` for subsequent requests.

### Environment Variables (recommended)

Store your credentials securely:

```bash
export INFISICAL_CLIENT_ID="your_client_id"
export INFISICAL_CLIENT_SECRET="your_client_secret"
export INFISICAL_BASE_URL="https://app.infisical.com"  # or your self-hosted URL
```

## Step 2: Authenticate and Get Access Token

```bash
# Get access token
TOKEN_RESPONSE=$(curl -s -X POST ${INFISICAL_BASE_URL}/api/v1/auth/machine-identity/login \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"${INFISICAL_CLIENT_ID}\",
    \"clientSecret\": \"${INFISICAL_CLIENT_SECRET}\"
  }")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)

echo "Access Token: $ACCESS_TOKEN"
```

## Step 3: List All Secrets in a Project Environment

Once authenticated, use the access token to list secrets:

```bash
curl -X GET https://app.infisical.com/api/v3/projects/YOUR_PROJECT_ID/secrets \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### With Environment Filter

To list secrets for a specific environment (e.g., "dev"):

```bash
curl -X GET "https://app.infisical.com/api/v3/projects/YOUR_PROJECT_ID/secrets?environment=dev" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response** (success):
```json
{
  "secrets": [
    {
      "id": "secret-id-1",
      "key": "DATABASE_URL",
      "value": "postgresql://...",
      "environment": "dev",
      "createdAt": "2026-04-10T14:30:00Z",
      "updatedAt": "2026-04-15T09:22:00Z",
      "metadata": {...}
    },
    {
      "id": "secret-id-2",
      "key": "API_KEY",
      "value": "sk_test_...",
      "environment": "dev",
      "createdAt": "2026-04-10T14:30:00Z",
      "updatedAt": "2026-04-15T09:22:00Z"
    }
  ]
}
```

## Complete Workflow Script

Here's a complete bash script combining both steps:

```bash
#!/bin/bash

# Configuration
INFISICAL_BASE_URL="${INFISICAL_BASE_URL:-https://app.infisical.com}"
CLIENT_ID="${INFISICAL_CLIENT_ID}"
CLIENT_SECRET="${INFISICAL_CLIENT_SECRET}"
PROJECT_ID="${INFISICAL_PROJECT_ID}"
ENVIRONMENT="${INFISICAL_ENVIRONMENT:-dev}"

# Validate inputs
if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" || -z "$PROJECT_ID" ]]; then
  echo "Error: Missing required environment variables"
  echo "Required: INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, INFISICAL_PROJECT_ID"
  exit 1
fi

# Step 1: Authenticate
echo "Authenticating with machine identity..."
TOKEN_RESPONSE=$(curl -s -X POST ${INFISICAL_BASE_URL}/api/v1/auth/machine-identity/login \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"${CLIENT_ID}\",
    \"clientSecret\": \"${CLIENT_SECRET}\"
  }")

# Extract access token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)

if [[ -z "$ACCESS_TOKEN" ]]; then
  echo "Error: Failed to obtain access token"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo "✓ Authentication successful"

# Step 2: List secrets
echo "Fetching secrets from project $PROJECT_ID (environment: $ENVIRONMENT)..."
SECRETS_RESPONSE=$(curl -s -X GET \
  "${INFISICAL_BASE_URL}/api/v3/projects/${PROJECT_ID}/secrets?environment=${ENVIRONMENT}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json")

echo "$SECRETS_RESPONSE" | jq '.' 2>/dev/null || echo "$SECRETS_RESPONSE"
```

Usage:
```bash
export INFISICAL_CLIENT_ID="your_client_id"
export INFISICAL_CLIENT_SECRET="your_client_secret"
export INFISICAL_PROJECT_ID="your_project_id"
export INFISICAL_ENVIRONMENT="dev"

chmod +x ./script.sh
./script.sh
```

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `clientId` | Machine identity client ID | `machine_abc123...` |
| `clientSecret` | Machine identity client secret | `secret_xyz789...` |
| `YOUR_PROJECT_ID` | Infisical project ID | `proj_12345...` |
| `environment` | Environment name (optional) | `dev`, `staging`, `prod` |

## Error Handling

### 401 Unauthorized
```json
{
  "statusCode": 401,
  "message": "Invalid credentials"
}
```
**Solution**: Verify `clientId` and `clientSecret` are correct.

### 403 Forbidden
```json
{
  "statusCode": 403,
  "message": "Access denied"
}
```
**Solution**: Ensure the machine identity has permission to access the project.

### 404 Not Found
```json
{
  "statusCode": 404,
  "message": "Project not found"
}
```
**Solution**: Verify `PROJECT_ID` is correct.

## Additional Notes

- **Token Expiry**: Tokens expire after `expiresIn` seconds (typically 3600 = 1 hour). Implement token refresh logic for long-running processes.
- **Base URL**: For self-hosted instances, replace `https://app.infisical.com` with your domain.
- **Pagination**: For large secret sets, use `?limit=100&offset=0` query parameters.
- **Encryption**: Secrets are encrypted at rest; use HTTPS for all API calls.
- **Rate Limiting**: Infisical API respects standard rate limits; implement exponential backoff for retries.

## API Version Note

- `v1` endpoint: Used for authentication
- `v3` endpoint: Used for secrets operations (recommended for current releases)

Refer to your Infisical instance's API documentation at `{your-domain}/api/docs` for the most up-to-date endpoint specifications.
