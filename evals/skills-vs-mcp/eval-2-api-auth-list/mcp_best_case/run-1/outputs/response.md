# Infisical REST API: Authentication and Secret Listing

Here's how to authenticate with Infisical's REST API using a machine identity and list all secrets in your project's dev environment.

## Step 1: Authenticate with Universal Auth

Use the Universal Auth Login endpoint with your machine identity credentials (clientId and clientSecret):

```bash
curl -X POST https://app.infisical.com/api/v1/auth/universal-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret"
  }'
```

**Response:**
```json
{
  "accessToken": "your-access-token"
}
```

Save the `accessToken` from the response — you'll use this to authenticate subsequent API requests.

## Step 2: List Secrets in Dev Environment

Use the List Secrets endpoint with your access token and project details:

```bash
curl -X GET "https://app.infisical.com/api/v4/secrets?projectId=your-project-id&environment=dev" \
  -H "Authorization: Bearer your-access-token"
```

**Query Parameters:**
- `projectId` (required): Your Infisical project ID
- `environment` (required): The environment slug (e.g., "dev", "staging", "prod")
- `secretPath` (optional): Filter secrets by path (e.g., "/app" or "/database")
- `offset` (optional): For pagination (default: 0)
- `limit` (optional): Number of secrets per page (default: varies)

**Example Response:**
```json
{
  "secrets": [
    {
      "id": "secret-id-1",
      "key": "DATABASE_URL",
      "value": "...",
      "environment": "dev",
      "secretPath": "/"
    },
    {
      "id": "secret-id-2",
      "key": "API_KEY",
      "value": "...",
      "environment": "dev",
      "secretPath": "/"
    }
  ]
}
```

## Complete Workflow Script

Here's a combined script that authenticates and lists secrets in one go:

```bash
#!/bin/bash

CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"
PROJECT_ID="your-project-id"
ENVIRONMENT="dev"
API_BASE="https://app.infisical.com"

# Step 1: Authenticate
echo "Authenticating..."
AUTH_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/universal-auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"clientId\": \"$CLIENT_ID\",
    \"clientSecret\": \"$CLIENT_SECRET\"
  }")

ACCESS_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"accessToken":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Authentication failed!"
  echo $AUTH_RESPONSE
  exit 1
fi

echo "Authentication successful!"

# Step 2: List secrets
echo "Fetching secrets from $ENVIRONMENT environment..."
curl -s -X GET "$API_BASE/api/v4/secrets?projectId=$PROJECT_ID&environment=$ENVIRONMENT" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
```

## Important Notes

- **API Versioning**: The API is versioned per-resource. Always use the latest available version (v4 for secrets, v1 for auth).
- **Rate Limits**: On Infisical Cloud, rate limits vary by plan. Self-hosted instances have no rate limits.
  - Free Plan: 200 reads/min, 90 writes/min, 120 secrets/min
  - Pro Plan: 350 reads/min, 200 writes/min, 300 secrets/min
- **Self-Hosted Instances**: If using a self-hosted Infisical instance, replace `https://app.infisical.com` with your instance URL.
- **Token Expiry**: Check your access token's expiry and refresh as needed based on your instance configuration.

## Troubleshooting

- **Invalid clientId/clientSecret**: Verify your machine identity credentials in the Infisical dashboard
- **401 Unauthorized**: Ensure your access token is included in the Authorization header with the "Bearer" prefix
- **404 on secrets endpoint**: Double-check your projectId and environment slug are correct
