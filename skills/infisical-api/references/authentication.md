# Authentication

Infisical supports multiple authentication methods. Machine identity Universal Auth is the recommended approach for production use.

## Universal Auth (Recommended)

Universal Auth is the preferred machine identity authentication method for all use cases.

### Login Endpoint

```
POST /api/v1/auth/universal-auth/login
```

### Request Body

```json
{
  "clientId": "string",
  "clientSecret": "string"
}
```

### Response

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600,
  "accessTokenMaxTTL": 86400,
  "tokenType": "Bearer"
}
```

### Example cURL

```bash
curl -X POST https://us.infisical.com/api/v1/auth/universal-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

### Using the Token

Include the token in all subsequent requests as a Bearer token:

```bash
curl -X GET https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Alternative Auth Methods

Infisical supports additional authentication methods for machine identities:

### AWS Auth

```
POST /api/v1/auth/aws-auth/login
```

Login with AWS IAM credentials. Useful for AWS-hosted applications.

### Azure Auth

```
POST /api/v1/auth/azure-auth/login
```

Login with Azure managed identity. Ideal for Azure-hosted applications.

### GCP Auth

```
POST /api/v1/auth/gcp-auth/login
```

Login with GCP service account. Recommended for Google Cloud deployments.

### Kubernetes Auth

```
POST /api/v1/auth/kubernetes-auth/login
```

Login with Kubernetes service account token. Perfect for containerized workloads.

### OIDC Auth

```
POST /api/v1/auth/oidc-auth/login
```

Login via OpenID Connect provider. Supports any OIDC-compliant provider.

### JWT Auth

```
POST /api/v1/auth/jwt-auth/login
```

Login with custom JWT. Useful for custom authentication systems.

### LDAP Auth

```
POST /api/v1/auth/ldap-auth/login
```

Login with LDAP credentials. Enterprise directory integration.

## Token Refresh

Access tokens expire after the `expiresIn` seconds returned in the login response. For long-lived integrations, implement token refresh logic:

```javascript
// Pseudocode for token refresh
let tokenExpiresAt = Date.now() + (expiresIn * 1000);

async function getValidToken() {
  if (Date.now() >= tokenExpiresAt - 60000) {
    // Refresh within 1 minute of expiry
    const response = await login(clientId, clientSecret);
    token = response.accessToken;
    tokenExpiresAt = Date.now() + (response.expiresIn * 1000);
  }
  return token;
}
```

The `accessTokenMaxTTL` value indicates the maximum lifetime of the token from issuance (typically 24 hours), which may be shorter than the server's token validity window.

## Deprecated: Service Tokens

Service tokens (prefixed with `st.`) are deprecated and should not be used in new code. They lack:
- Fine-grained permission controls
- Machine identity features
- Audit logging capabilities
- Rotation enforcement

Migrate all service token usage to machine identities with Universal Auth.

## Region Selection

Choose the appropriate Infisical region endpoint:

- **US Region**: `https://us.infisical.com`
- **EU Region**: `https://eu.infisical.com`
- **Self-Hosted**: Use your custom domain (e.g., `https://secrets.mycompany.com`)

## Headers

All authentication requests must include:

```
Content-Type: application/json
```

## Common Issues

### 401 Unauthorized

- Verify clientId and clientSecret are correct
- Confirm the token hasn't expired
- Check that the Bearer token is included in the Authorization header

### 403 Forbidden

- Machine identity may not have permission for the requested resource
- Verify identity auth method is configured for the project
- Check role-based access controls (RBAC) in the project

### 404 Not Found

- Confirm you're using the correct endpoint URL
- Verify the projectId exists and is accessible
- Check that the region (us.infisical.com vs eu.infisical.com) matches your deployment
