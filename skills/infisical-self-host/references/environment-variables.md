# Environment Variables Reference

This guide covers all environment variables used to configure Infisical self-hosted deployments.

## Essential Security Keys

### ENCRYPTION_KEY
**Required** – Master encryption key for all secrets at rest.

- **Format**: 16 bytes as hex (32 hex characters)
- **Example**: `a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8`
- **Generation**: `openssl rand -hex 16`
- **Critical Notes**:
  - Cannot be recovered if lost
  - Must be stable across deployments and upgrades
  - Rotate using Infisical's key rotation procedures (enterprise feature)
  - Back up securely in a separate location

### AUTH_SECRET
**Required** – Secret key for signing session tokens and JWTs.

- **Format**: 32 bytes as base64
- **Example**: `VUJrQV9FbmNyeXB0aW9uS2V5XzMyQnl0ZXNfQmFzZTY0RW5jb2RlZA==`
- **Generation**: `openssl rand -base64 32`
- **Notes**:
  - Used for all authentication tokens
  - Must be stable and unique per deployment

## Database Configuration

### DB_CONNECTION_URI
**Required** – PostgreSQL connection string.

- **Format**: `postgresql://user:password@host:port/database`
- **Example**: `postgresql://infisical:secret@postgres.example.com:5432/infisical`
- **Requirements**:
  - PostgreSQL 14 or newer
  - `uuid-ossp` extension enabled: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
  - `pgcrypto` extension enabled: `CREATE EXTENSION IF NOT EXISTS pgcrypto;`

### DB_ROOT_CERT
Optional – Base64-encoded PEM certificate for SSL/TLS verification of PostgreSQL.

- **Format**: Base64-encoded SSL certificate
- **Usage**: For databases with self-signed or custom CA certificates
- **Example**: 
  ```bash
  cat /path/to/ca.pem | base64 -w 0
  ```
- **Notes**: Verify SSL/TLS connections for managed database services (RDS, Cloud SQL, Azure Database)

### DB_READ_REPLICAS
Optional – JSON array of read-only database replicas.

- **Format**: JSON array of connection objects
- **Example**:
  ```json
  [
    {"connectionString": "postgresql://user:pass@replica1:5432/infisical"},
    {"connectionString": "postgresql://user:pass@replica2:5432/infisical"}
  ]
  ```
- **Use Case**: Distribute read-heavy workloads across multiple database replicas
- **Requirements**: Read replicas must be in sync with primary

## Redis Configuration

### REDIS_URL
**Required** – Redis connection string.

- **Format**: `redis://[:password@]host:port[/db]` or `rediss://...` for TLS
- **Examples**:
  - Standard: `redis://redis.example.com:6379`
  - With auth: `redis://:password@redis.example.com:6379`
  - TLS: `rediss://redis.example.com:6380`
- **Requirements**: Redis 6.2 or newer
- **Important**: Redis Cluster mode is NOT supported; use standalone or Sentinel

### Redis Sentinel (High Availability)

Use these variables to configure Redis Sentinel for HA without Cluster mode.

#### REDIS_SENTINEL_HOSTS
Comma-separated list of Sentinel node addresses.

- **Format**: `host1:port1,host2:port2,host3:port3`
- **Example**: `sentinel1.example.com:26379,sentinel2.example.com:26379,sentinel3.example.com:26379`

#### REDIS_SENTINEL_MASTER_NAME
Name of the Redis master monitored by Sentinel.

- **Example**: `mymaster`
- **Default**: `mymaster` (if not specified)

#### REDIS_SENTINEL_ENABLE_TLS
Enable TLS for Sentinel connections.

- **Format**: `true` or `false`
- **Default**: `false`

#### REDIS_SENTINEL_USERNAME
Username for Sentinel authentication (if required).

#### REDIS_SENTINEL_PASSWORD
Password for Sentinel authentication.

## SMTP Configuration

SMTP is required for email-based features. Without SMTP configured, the following features are disabled:
- Multi-factor authentication (MFA) via email
- Email invitations
- Suspicious login alerts
- Password reset emails

### SMTP_HOST
**Required if SMTP enabled** – SMTP server hostname.

- **Example**: `smtp.gmail.com`

### SMTP_PORT
SMTP server port.

- **Default**: `587` (STARTTLS)
- **Common Values**:
  - `587` — STARTTLS (recommended)
  - `465` — SMTPS (implicit TLS)
  - `25` — Unencrypted (not recommended for production)

### SMTP_USERNAME
Username for SMTP authentication.

### SMTP_PASSWORD
Password for SMTP authentication.

### SMTP_FROM_ADDRESS
**Required if SMTP enabled** – Email address from which emails are sent.

- **Example**: `noreply@infisical.com`

### SMTP_FROM_NAME
Display name for the sender.

- **Example**: `Infisical`
- **Default**: `Infisical`

### SMTP_REQUIRE_TLS
Require TLS connection (STARTTLS).

- **Format**: `true` or `false`
- **Default**: `true`

### SMTP_IGNORE_TLS
Ignore TLS certificate errors (useful for self-signed certificates in development).

- **Format**: `true` or `false`
- **Default**: `false`
- **Warning**: Do not use in production

## OAuth/SSO Configuration

### Google Login
To enable Google OAuth login, register an OAuth 2.0 application in Google Cloud Console.

#### CLIENT_ID_GOOGLE_LOGIN
Google OAuth client ID.

#### CLIENT_SECRET_GOOGLE_LOGIN
Google OAuth client secret.

### GitHub Login
Register an OAuth application at https://github.com/settings/developers.

#### CLIENT_ID_GITHUB_LOGIN
GitHub OAuth client ID.

#### CLIENT_SECRET_GITHUB_LOGIN
GitHub OAuth client secret.

### GitLab Login
Register an OAuth application in your GitLab instance (or gitlab.com).

#### CLIENT_ID_GITLAB_LOGIN
GitLab OAuth client ID.

#### CLIENT_SECRET_GITLAB_LOGIN
GitLab OAuth client secret.

## Authentication Timeouts

### JWT_AUTH_LIFETIME
Lifetime of access tokens.

- **Default**: `15m` (15 minutes)
- **Format**: Valid Node.js duration string (e.g., `30m`, `1h`)

### JWT_REFRESH_LIFETIME
Lifetime of refresh tokens.

- **Default**: `24h` (24 hours)
- **Format**: Valid Node.js duration string

## Enterprise and Licensing

### LICENSE_KEY
License key for Infisical Enterprise features.

- **Format**: Provided by Infisical upon enterprise subscription
- **Features Enabled**: SAML, RBAC advanced features, audit logs, IP allowlisting, etc.

## FIPS 140-2 Compliance

FIPS mode is enabled using the `infisical/infisical:latest-fips` image with additional Node.js configuration.

### FIPS_ENABLED
Enable FIPS 140-2 mode.

- **Format**: `true` or `false`
- **Default**: `false`
- **Requirement**: Must use `infisical/infisical:latest-fips` image

### NODE_OPTIONS
Node.js runtime options for FIPS compliance.

- **For FIPS Mode**:
  ```
  NODE_OPTIONS="--max-old-space-size=8192 --force-fips"
  ```
- **Notes**:
  - `--force-fips` enables FIPS mode
  - `--max-old-space-size` allocates memory for the Node.js heap (adjust based on load)

## Telemetry

### TELEMETRY_ENABLED
Enable or disable telemetry collection.

- **Format**: `true` or `false`
- **Default**: `true`

### OTEL_EXPORT_TYPE
Export destination for OpenTelemetry metrics.

- **Options**: `prometheus`, `otlp`
- **Example**: `prometheus` exports metrics on `/metrics` endpoint for Prometheus scraping

## Web and Security

### SITE_URL
**Required** – Public URL of the Infisical instance.

- **Format**: Full URL (e.g., `https://secrets.example.com`)
- **Usage**: Used for email links, OAuth redirects, and frontend configuration

### CORS_ALLOWED_ORIGINS
Comma-separated list of allowed CORS origins.

- **Format**: Full URLs (e.g., `https://app.example.com,https://admin.example.com`)
- **Default**: Allows same origin
- **Notes**: Whitelist specific origins in production; avoid wildcards (`*`)

### ALLOW_INTERNAL_IP_CONNECTIONS
Allow connections to internal IP addresses (useful for Kubernetes).

- **Format**: `true` or `false`
- **Default**: `false`
- **Use Case**: Kubernetes nodes using internal IPs, local Redis/PostgreSQL on private networks

## Summary: Minimal Configuration

For a minimal production deployment, these environment variables are required:

```bash
# Security
ENCRYPTION_KEY="<16-byte-hex>"
AUTH_SECRET="<base64-32-byte>"

# Database
DB_CONNECTION_URI="postgresql://user:pass@host:5432/infisical"

# Redis
REDIS_URL="redis://host:6379"

# Web
SITE_URL="https://secrets.example.com"

# SMTP (required for email features)
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USERNAME="user@example.com"
SMTP_PASSWORD="password"
SMTP_FROM_ADDRESS="noreply@example.com"
```

For additional features (OAuth, FIPS, Sentinel, etc.), add the relevant variables from the sections above.
