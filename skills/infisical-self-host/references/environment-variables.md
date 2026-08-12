# Environment Variables Reference

This guide covers all environment variables used to configure Infisical self-hosted deployments.

## Essential Security Keys

### ENCRYPTION_KEY
**Required** – Master encryption key for all secrets at rest.

**The format depends on whether FIPS mode is enabled.**

| Mode | Format | Generation |
|------|--------|-----------|
| Standard | 16-byte hex string (32 hex chars) | `openssl rand -hex 16` |
| **FIPS-enabled** | **256-bit base64-encoded key** | `openssl rand -base64 32` |

- **Standard example**: `a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8`
- **Critical Notes**:
  - Cannot be recovered if lost
  - Must be stable across deployments and upgrades
  - Rotate using Infisical's key rotation procedures (enterprise feature)
  - Back up securely in a separate location
  - Do not carry a hex key into a FIPS deployment — generate a base64 256-bit key instead

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

Redis is a **required, persistent datastore** — not merely a cache. It holds the background job
queue, distributed locks, cross-instance coordination state for scheduled jobs, and rate-limit
counters. A running instance is degraded for as long as Redis is unreachable.

**The instance will not start unless exactly one of these is set:** `REDIS_URL`,
`REDIS_SENTINEL_HOSTS`, or `REDIS_CLUSTER_HOSTS`. All three topologies are supported —
standalone, Sentinel, and Cluster.

### REDIS_URL
Redis connection string — the standalone option.

- **Format**: `redis://[:password@]host:port[/db]` or `rediss://...` for TLS
- **Examples**:
  - Standard: `redis://redis.example.com:6379`
  - With auth: `redis://:password@redis.example.com:6379`
  - TLS: `rediss://redis.example.com:6380`
- **Requirements**: Redis 6.x or 7.x; at least 6.2 is advised

### Redis Cluster

#### REDIS_CLUSTER_HOSTS
Comma-separated list of Redis Cluster `host:port` pairs.

- **Example**: `192.168.65.254:26379,192.168.65.254:26380`

#### REDIS_CLUSTER_ENABLE_TLS
Enable TLS on the cluster connection.

- **Format**: `true` or `false`
- **Default**: `false`

#### REDIS_CLUSTER_AWS_ELASTICACHE_DNS_LOOKUP_MODE
DNS lookup mode for AWS ElastiCache cluster endpoints.

- **Default**: `false`

### TLS with a private CA

If your Redis server uses a certificate signed by a private CA or a self-signed certificate, point
`NODE_EXTRA_CA_CERTS` at the CA file:

```bash
REDIS_URL=rediss://your-redis-host:6379
NODE_EXTRA_CA_CERTS=/path/to/ca.crt
```

For Sentinel or Cluster, enable TLS with `REDIS_SENTINEL_ENABLE_TLS` or
`REDIS_CLUSTER_ENABLE_TLS` respectively.

### Required Redis server settings

These are configured on the Redis server itself, not via Infisical environment variables:

| Setting | Value | Why |
|---------|-------|-----|
| `maxmemory-policy` | `noeviction` | **Required.** Redis holds queue and coordination state; evicting keys under memory pressure would silently drop work |
| Persistence | AOF, or RDB snapshots at minimum | Pending secret rotations, syncs, and webhook deliveries live in Redis — a Redis that returns empty loses them |

Include Redis in your backup strategy, and give it the same availability target as the Infisical
instances themselves. A single unreplicated Redis is a single point of failure for the whole
deployment.

Sizing is modest: 2 vCPU, 4 GB RAM, and a 30 GB SSD suffices for small deployments.

An **active-passive** setup is recommended. Active-active has not been tested.

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

## FIPS 140-3 Compliance

Infisical is compliant with **FIPS 140-3**, using validated cryptographic modules for all
encryption operations within the FIPS boundary.

FIPS mode requires the **separate `infisical/infisical-fips` Docker image** — an Enterprise-only
image on its own Docker Hub repository. It is not a tag on the standard `infisical/infisical`
repository.

```bash
docker pull infisical/infisical-fips
```

### FIPS_ENABLED
Enable FIPS 140-3 mode.

- **Format**: `true` or `false`
- **Default**: `false`
- **Requirement**: Must use the `infisical/infisical-fips` image
- **Also required**: `ENCRYPTION_KEY` must be a 256-bit base64 key (`openssl rand -base64 32`), not the standard hex format

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

A minimal self-hosted instance needs at least `ENCRYPTION_KEY`, `AUTH_SECRET`,
`DB_CONNECTION_URI`, and `REDIS_URL` defined. Add `SITE_URL` and SMTP for a usable production
deployment:

```bash
# Security — generate with:
#   openssl rand -hex 16     (standard)
#   openssl rand -base64 32  (FIPS mode, and for AUTH_SECRET)
ENCRYPTION_KEY="<16-byte-hex>"        # 256-bit base64 if FIPS_ENABLED=true
AUTH_SECRET="<base64-32-byte>"

# Database (PostgreSQL 14+; tested on 16)
DB_CONNECTION_URI="postgresql://user:pass@host:5432/infisical"

# Redis — required; server must have maxmemory-policy=noeviction
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
