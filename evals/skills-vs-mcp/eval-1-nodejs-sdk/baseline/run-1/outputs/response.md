# Setting Up the Infisical Node.js SDK in Express

This guide walks you through installing, initializing, and using the Infisical Node.js SDK to load secrets when your Express server starts.

## Installation

Install the Infisical SDK from npm:

```bash
npm install @infisical/sdk
```

Or with yarn:

```bash
yarn add @infisical/sdk
```

## Basic Setup in Express

Here's a complete example of initializing Infisical and loading secrets when your server starts:

```javascript
import express from 'express';
import { InfisicalClient } from '@infisical/sdk';

const app = express();
let secrets = {};

// Initialize Infisical client and load secrets
async function initializeSecrets() {
  const client = new InfisicalClient({
    auth: {
      universalAuth: {
        clientId: process.env.INFISICAL_CLIENT_ID,
        clientSecret: process.env.INFISICAL_CLIENT_SECRET,
      },
    },
  });

  try {
    // List all secrets in your project
    const secretsList = await client.listSecrets({
      projectId: process.env.INFISICAL_PROJECT_ID,
      environment: process.env.INFISICAL_ENVIRONMENT || 'dev',
    });

    // Convert array to object for easy access
    secretsList.secrets.forEach((secret) => {
      secrets[secret.secretKey] = secret.secretValue;
    });

    console.log(`✓ Loaded ${Object.keys(secrets).length} secrets from Infisical`);
  } catch (error) {
    console.error('Failed to load secrets from Infisical:', error);
    process.exit(1);
  }
}

// Load secrets before starting server
await initializeSecrets();

// Example route using loaded secrets
app.get('/api/status', (req, res) => {
  res.json({
    status: 'ok',
    apiKey: secrets.API_KEY ? '***' : 'not loaded',
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## Authentication Methods

### Universal Auth (Recommended)

Universal Auth is ideal for service-to-service authentication:

```javascript
const client = new InfisicalClient({
  auth: {
    universalAuth: {
      clientId: process.env.INFISICAL_CLIENT_ID,
      clientSecret: process.env.INFISICAL_CLIENT_SECRET,
    },
  },
});
```

### API Key Authentication

For simpler scenarios, you can use an API key:

```javascript
const client = new InfisicalClient({
  auth: {
    apiKey: process.env.INFISICAL_API_KEY,
  },
});
```

## Listing All Secrets

The `listSecrets()` method retrieves all secrets for a given project and environment:

```javascript
async function listAllSecrets() {
  const client = new InfisicalClient({
    auth: {
      universalAuth: {
        clientId: process.env.INFISICAL_CLIENT_ID,
        clientSecret: process.env.INFISICAL_CLIENT_SECRET,
      },
    },
  });

  const secretsList = await client.listSecrets({
    projectId: 'your-project-id',
    environment: 'dev', // or 'prod', 'staging', etc.
  });

  console.log('All secrets:');
  secretsList.secrets.forEach((secret) => {
    console.log(`- ${secret.secretKey}: ${secret.secretValue}`);
  });

  return secretsList.secrets;
}
```

## Getting Individual Secrets

You can also retrieve a single secret by key:

```javascript
const secret = await client.getSecret({
  secretKey: 'DATABASE_URL',
  projectId: process.env.INFISICAL_PROJECT_ID,
  environment: process.env.INFISICAL_ENVIRONMENT,
});

console.log(secret.secretValue);
```

## Environment Configuration

Store your credentials in a `.env` file (or your hosting platform's environment variables):

```
INFISICAL_CLIENT_ID=your-client-id
INFISICAL_CLIENT_SECRET=your-client-secret
INFISICAL_PROJECT_ID=your-project-id
INFISICAL_ENVIRONMENT=dev
PORT=3000
```

**Important**: Never commit `.env` to version control. Use a `.gitignore`:

```
.env
.env.local
```

## Complete Example with Error Handling

```javascript
import express from 'express';
import { InfisicalClient } from '@infisical/sdk';

const app = express();
let secrets = {};
let isReady = false;

async function initializeSecrets() {
  if (!process.env.INFISICAL_CLIENT_ID || !process.env.INFISICAL_CLIENT_SECRET) {
    console.warn('Infisical credentials not configured. Skipping secret loading.');
    return;
  }

  const client = new InfisicalClient({
    auth: {
      universalAuth: {
        clientId: process.env.INFISICAL_CLIENT_ID,
        clientSecret: process.env.INFISICAL_CLIENT_SECRET,
      },
    },
  });

  try {
    const secretsList = await client.listSecrets({
      projectId: process.env.INFISICAL_PROJECT_ID,
      environment: process.env.INFISICAL_ENVIRONMENT || 'dev',
    });

    secretsList.secrets.forEach((secret) => {
      secrets[secret.secretKey] = secret.secretValue;
    });

    isReady = true;
    console.log(`✓ Loaded ${Object.keys(secrets).length} secrets from Infisical`);
  } catch (error) {
    console.error('Failed to load secrets:', error.message);
    // In production, you might want to exit. In dev, you can continue.
    if (process.env.NODE_ENV === 'production') {
      process.exit(1);
    }
  }
}

// Health check middleware
app.use((req, res, next) => {
  if (!isReady && process.env.INFISICAL_CLIENT_ID) {
    return res.status(503).json({ error: 'Secrets not loaded yet' });
  }
  next();
});

app.get('/secrets/:key', (req, res) => {
  const { key } = req.params;
  if (secrets.hasOwnProperty(key)) {
    res.json({ key, value: '***' }); // Don't expose actual values
  } else {
    res.status(404).json({ error: `Secret "${key}" not found` });
  }
});

// Initialize and start server
await initializeSecrets();

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

## TypeScript Support

The Infisical SDK includes TypeScript types out of the box:

```typescript
import express, { Express } from 'express';
import { InfisicalClient, SecretSchema } from '@infisical/sdk';

interface SecretsMap {
  [key: string]: string;
}

const app: Express = express();
const secrets: SecretsMap = {};

async function initializeSecrets(): Promise<void> {
  const client = new InfisicalClient({
    auth: {
      universalAuth: {
        clientId: process.env.INFISICAL_CLIENT_ID!,
        clientSecret: process.env.INFISICAL_CLIENT_SECRET!,
      },
    },
  });

  const secretsList = await client.listSecrets({
    projectId: process.env.INFISICAL_PROJECT_ID!,
    environment: process.env.INFISICAL_ENVIRONMENT || 'dev',
  });

  secretsList.secrets.forEach((secret: SecretSchema) => {
    secrets[secret.secretKey] = secret.secretValue;
  });
}

await initializeSecrets();
app.listen(3000);
```

## Key Points

1. **Initialize before starting the server** — Load secrets during the startup phase, not on first request.
2. **Use Universal Auth for services** — It's more secure than API keys for server-to-server communication.
3. **Handle errors gracefully** — Decide whether missing secrets should crash your app or allow graceful degradation.
4. **Never log actual secret values** — Always mask them in logs and API responses.
5. **Cache secrets in memory** — Once loaded, secrets are available instantly without additional API calls.
6. **Keep credentials in environment variables** — Never hardcode client IDs or secrets.

For more information, refer to the official Infisical documentation and SDK repository.
