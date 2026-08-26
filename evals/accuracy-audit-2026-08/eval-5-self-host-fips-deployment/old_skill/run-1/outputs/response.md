Based on the Infisical self-host skill reference, here's the FIPS-compliant Docker deployment.

## Image

Pull the FIPS variant, not the standard image:

```bash
docker pull infisical/infisical:latest-fips
```

## FIPS standard

Infisical's FIPS image is compliant with **FIPS 140-2**.

## Encryption key generation

```bash
ENCRYPTION_KEY=$(openssl rand -hex 16)
```

This produces 16 bytes as 32 hex characters. Notes:
- It's the master key encrypting all secrets at rest.
- It **cannot be recovered if lost** — back it up securely in a separate location from the deployment itself.
- It must stay stable across restarts/upgrades. Don't regenerate it after go-live; rotating it requires Infisical's key rotation procedure (enterprise feature).

## Required environment variables

```bash
# FIPS mode
FIPS_ENABLED=true
NODE_OPTIONS="--max-old-space-size=8192 --force-fips"

# Security keys
ENCRYPTION_KEY=$(openssl rand -hex 16)          # 16 bytes hex
AUTH_SECRET=$(openssl rand -base64 32)          # 32 bytes base64

# Database (Postgres 14+, uuid-ossp and pgcrypto extensions enabled)
DB_CONNECTION_URI="postgresql://user:password@postgres.example.com:5432/infisical"

# Redis (6.2+, standalone or Sentinel — cluster mode NOT supported)
REDIS_URL="redis://redis.example.com:6379"

# Public URL
SITE_URL="https://secrets.example.com"

# SMTP (required for MFA-via-email, invites, password reset, login alerts)
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USERNAME="user@example.com"
SMTP_PASSWORD="password"
SMTP_FROM_ADDRESS="noreply@example.com"
```

## Run it

```bash
docker run -d \
  --name infisical \
  --env-file .env \
  -p 8080:8080 \
  infisical/infisical:latest-fips
```

Verify with `curl http://localhost:8080/api/status` (expects HTTP 200).

A couple of things worth confirming with your compliance team before you commit to this: whether the underlying PostgreSQL and Redis you point at also need to run in FIPS-validated configurations for your attestation to hold end to end, since the skill only covers the Infisical container itself.
