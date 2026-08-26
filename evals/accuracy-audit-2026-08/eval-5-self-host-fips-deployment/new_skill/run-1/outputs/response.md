Here's the FIPS-compliant Docker deployment for Infisical.

## Image

Pull the separate FIPS image, not the standard repo:

```bash
docker pull infisical/infisical-fips
```

This is an Enterprise-only image on its own Docker Hub repository. FIPS mode is not available as a tag on `infisical/infisical`.

## Compliance Standard

Infisical is compliant with **FIPS 140-3**.

## Encryption Key Generation

FIPS mode changes the `ENCRYPTION_KEY` format from the standard 16-byte hex to a **256-bit base64 key**:

```bash
openssl rand -base64 32
```

Do not carry over a hex key from a standard deployment. It won't work in FIPS mode.

## Required Environment Variables

```bash
# FIPS mode
FIPS_ENABLED=true
NODE_OPTIONS="--max-old-space-size=8192 --force-fips"

# Encryption (256-bit base64, not hex, because FIPS_ENABLED=true)
ENCRYPTION_KEY="$(openssl rand -base64 32)"

# Session/JWT signing (same in FIPS and standard mode)
AUTH_SECRET="$(openssl rand -base64 32)"

# Database (PostgreSQL 14+, tested on 16)
DB_CONNECTION_URI="postgresql://user:password@postgres.example.com:5432/infisical"

# Redis is required, not optional — the instance won't start without one of these
REDIS_URL="redis://redis.example.com:6379"

# Public URL
SITE_URL="https://secrets.example.com"

# SMTP (required for MFA-via-email, invites, password resets, login alerts)
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USERNAME="user@example.com"
SMTP_PASSWORD="password"
SMTP_FROM_ADDRESS="noreply@example.com"
```

## Run

```bash
docker run -d \
  --name infisical \
  --env-file .env \
  -p 8080:8080 \
  infisical/infisical-fips
```

Two things worth flagging before you go further: your Redis server needs `maxmemory-policy=noeviction` set directly on the Redis config (not an Infisical env var), and since Redis holds queue state and rotation/sync data, make sure it's backed up and has real availability, not just a single container.
