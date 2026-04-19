# Setting Up Infisical Node.js SDK in Express

This guide covers installation, initialization, authentication, and secret retrieval for your Express application.

## Requirements

- Node.js 20 or higher (v5 of the SDK)
- An Infisical instance (self-hosted or cloud)
- Machine identity credentials (Client ID and Client Secret)

## Installation

Install the Infisical SDK via npm:

```bash
npm install @infisical/sdk
```

Ensure your `package.json` specifies Node.js 20+ in the engines field:

```json
{
  "engines": {
    "node": ">=20.0.0"
  }
}
```

## Basic Setup in Express

Here's a complete example of initializing the SDK and loading secrets on server start:

```typescript
import express from 'express';
import { InfisicalSDK } from '@infisical/sdk';

const app = express();
let infisicalClient: InfisicalSDK;

// Initialize Infisical client and authenticate on server startup
async function initializeSecrets() {
  try {
    // Create SDK instance
    infisicalClient = new InfisicalSDK({
      siteUrl: process.env.INFISICAL_URL || "https://app.infisical.com"
    });

    // Authenticate using Machine Identity (Universal Auth)
    await infisicalClient.auth().universalAuth.login({
      clientId: process.env.INFISICAL_CLIENT_ID!,
      clientSecret: process.env.INFISICAL_CLIENT_SECRET!
    });

    console.log('✓ Successfully authenticated with Infisical');

    // Load all secrets from the specified environment
    const allSecrets = await infisicalClient.secrets().listSecrets({
      environment: process.env.INFISICAL_ENVIRONMENT || "dev",
      projectId: process.env.INFISICAL_PROJECT_ID!
    });

    console.log(`✓ Loaded ${allSecrets.length} secrets`);

    // Optional: Log secret names (not values for security)
    allSecrets.forEach(secret => {
      console.log(`  - ${secret.secretKey}`);
    });

    return allSecrets;
  } catch (error) {
    console.error('✗ Failed to initialize Infisical:', error);
    throw error;
  }
}

// Start server
async function startServer() {
  try {
    await initializeSecrets();

    app.get('/health', (req, res) => {
      res.json({ status: 'ok' });
    });

    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`✓ Express server running on port ${PORT}`);
    });
  } catch (error) {
    console.error('✗ Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
```

## Environment Variables

Create a `.env` file with the following credentials:

```
INFISICAL_URL=https://your-infisical-instance.com
INFISICAL_CLIENT_ID=your-machine-identity-client-id
INFISICAL_CLIENT_SECRET=your-machine-identity-client-secret
INFISICAL_PROJECT_ID=your-project-id
INFISICAL_ENVIRONMENT=dev
PORT=3000
```

> **Security Note**: Never commit `.env` files to version control. Use a secrets manager or CI/CD platform to inject these in production.

## Core Methods Available

Once authenticated, you have access to the following secret management operations:

### List Secrets
```typescript
const secrets = await infisicalClient.secrets().listSecrets({
  environment: "dev",
  projectId: "<project-id>"
});
```

### Get a Single Secret
```typescript
const secret = await infisicalClient.secrets().getSecret({
  secretKey: "DATABASE_URL",
  environment: "dev",
  projectId: "<project-id>"
});
console.log(secret.secretValue);
```

### Create a Secret
```typescript
const newSecret = await infisicalClient.secrets().createSecret({
  secretKey: "API_KEY",
  secretValue: "your-api-key",
  environment: "dev",
  projectId: "<project-id>"
});
```

### Update a Secret
```typescript
const updated = await infisicalClient.secrets().updateSecret({
  secretKey: "API_KEY",
  secretValue: "new-api-key-value",
  environment: "dev",
  projectId: "<project-id>"
});
```

### Delete a Secret
```typescript
await infisicalClient.secrets().deleteSecret({
  secretKey: "API_KEY",
  environment: "dev",
  projectId: "<project-id>"
});
```

## Advanced Features

The SDK also supports:

- **Dynamic Secrets**: Generate temporary credentials on-the-fly
- **Folders**: Organize secrets in a hierarchical structure
- **Projects & Environments**: Manage multiple deployment configurations
- **KMS**: Key management operations

Refer to the official [Infisical Node.js SDK documentation](https://infisical.com/docs/sdk/nodejs) for detailed information on these features.

## Error Handling

Always wrap SDK calls in try-catch blocks:

```typescript
try {
  const secrets = await infisicalClient.secrets().listSecrets({
    environment: "prod",
    projectId: "<project-id>"
  });
} catch (error) {
  if (error instanceof Error) {
    console.error('Error fetching secrets:', error.message);
  }
  // Handle authentication errors, network issues, etc.
}
```

## Version Support

- **v5+**: Requires Node.js 20+
- **v4 and earlier**: Officially unsupported — upgrade to v5 for security and stability

## Next Steps

1. Obtain Machine Identity credentials from your Infisical dashboard
2. Set environment variables in your deployment platform
3. Test the connection locally before deploying
4. Monitor logs to ensure secrets load successfully on startup
