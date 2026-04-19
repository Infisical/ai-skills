# Setting Up Infisical Node.js SDK in Express

This guide covers complete setup of the Infisical SDK in an Express app to load secrets at server startup.

## Installation

First, install the SDK. Note: requires Node.js 20+ for v5+:

```bash
npm install @infisical/sdk
```

Verify your Node.js version:
```bash
node --version  # Should be v20.0.0 or higher
```

## Basic Setup

Create a new file `src/secrets.js` to handle secret initialization:

```typescript
import { InfisicalSDK } from '@infisical/sdk';

let secretsCache = {};

export async function initializeSecrets() {
  const client = new InfisicalSDK({
    siteUrl: "https://app.infisical.com" // or your self-hosted URL
  });

  // Authenticate using machine identity credentials
  await client.auth().universalAuth.login({
    clientId: process.env.INFISICAL_CLIENT_ID,
    clientSecret: process.env.INFISICAL_CLIENT_SECRET
  });

  // List all secrets from your environment
  const secrets = await client.secrets().listSecrets({
    environment: process.env.INFISICAL_ENVIRONMENT || "dev",
    projectId: process.env.INFISICAL_PROJECT_ID,
    secretPath: "/"
  });

  // Cache secrets in memory
  secrets.forEach(secret => {
    secretsCache[secret.secretKey] = secret.secretValue;
  });

  console.log(`✓ Loaded ${secrets.length} secrets from Infisical`);
  
  return secretsCache;
}

export function getSecret(key) {
  if (!secretsCache[key]) {
    throw new Error(`Secret "${key}" not found in cache`);
  }
  return secretsCache[key];
}

export function getAllSecrets() {
  return { ...secretsCache };
}
```

## Express App Integration

Update your Express app (`src/server.js` or `src/app.js`):

```typescript
import express from 'express';
import { initializeSecrets, getSecret } from './secrets.js';

const app = express();

// Initialize secrets before starting server
async function startServer() {
  try {
    // Load all secrets on startup
    await initializeSecrets();
    
    // Now you can use secrets throughout your app
    const dbUrl = getSecret('DATABASE_URL');
    const apiKey = getSecret('THIRD_PARTY_API_KEY');
    
    // Example route using secrets
    app.get('/health', (req, res) => {
      res.json({ status: 'ok' });
    });
    
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`✓ Server running on port ${PORT}`);
    });
    
  } catch (error) {
    console.error('✗ Failed to start server:', error.message);
    process.exit(1);
  }
}

startServer();
```

## Environment Setup

Create a `.env` file (or configure in your deployment environment):

```env
INFISICAL_CLIENT_ID=your-machine-identity-client-id
INFISICAL_CLIENT_SECRET=your-machine-identity-client-secret
INFISICAL_PROJECT_ID=your-project-id
INFISICAL_ENVIRONMENT=dev
INFISICAL_SITE_URL=https://app.infisical.com
PORT=3000
```

**Important**: Never commit `.env` to version control. Use secure credential management for production.

## Complete Example: Express App with Database

Here's a full example showing how to use secrets for database connection:

```typescript
import express from 'express';
import pg from 'pg';
import { initializeSecrets, getSecret } from './secrets.js';

const app = express();

async function startServer() {
  try {
    // Load secrets
    console.log('Loading secrets from Infisical...');
    await initializeSecrets();
    
    // Initialize database with loaded secret
    const dbUrl = getSecret('DATABASE_URL');
    const pool = new pg.Pool({ connectionString: dbUrl });
    
    // Test connection
    const client = await pool.connect();
    await client.query('SELECT NOW()');
    client.release();
    console.log('✓ Database connected');
    
    // Routes
    app.get('/api/data', async (req, res) => {
      try {
        const client = await pool.connect();
        const result = await client.query('SELECT * FROM users LIMIT 10');
        client.release();
        res.json(result.rows);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    
    // Error handling
    app.use((err, req, res, next) => {
      console.error(err);
      res.status(500).json({ error: 'Internal server error' });
    });
    
    // Start server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`✓ Server running on port ${PORT}`);
    });
    
  } catch (error) {
    console.error('✗ Server startup failed:', error.message);
    process.exit(1);
  }
}

startServer();
```

## Key Points

### Authentication Best Practice
- **Use machine identities** (recommended): Create a machine identity in Infisical and use `universalAuth.login()` with client credentials
- **Avoid deprecated methods**: Service Tokens (st.* prefix) and API Keys are deprecated — don't use them in new code
- **Zero-secret auth** (when possible): For cloud deployments, prefer native auth methods:
  - AWS EC2 → AWS Auth
  - Kubernetes → Kubernetes Auth
  - GitHub Actions → OIDC Auth

### Caching Strategy
The example caches secrets in memory at startup. For production:
- **Pros**: Fast access, no repeated API calls
- **Cons**: Secrets don't auto-update if changed in Infisical
- **Solution**: Implement a refresh interval or restart the app to reload secrets

### Error Handling
Always wrap initialization in try-catch to ensure:
- Missing credentials are caught early
- Database or network errors don't silently fail
- Server exits with status 1 on failure (important for container orchestration)

## Next Steps

1. **Create machine identity in Infisical**: Go to Project Settings → Machine Identities → Create
2. **Set environment variables** in your deployment platform
3. **Test locally** with `.env` before deploying
4. **Monitor logs** to verify secrets load successfully on startup

For more details, see the [Infisical documentation](https://infisical.com/docs) or refer to the SDK repository.
