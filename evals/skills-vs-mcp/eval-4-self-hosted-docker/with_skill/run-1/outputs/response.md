# Production-Ready Docker Compose for Infisical Self-Hosting

Below is a complete, production-ready `docker-compose.yml` configuration for self-hosting Infisical with proper encryption, security setup, and best practices.

## Prerequisites

Before running this configuration, generate the required encryption and authentication secrets:

```bash
# Generate ENCRYPTION_KEY (16 bytes = 32 hex characters)
openssl rand -hex 16

# Generate AUTH_SECRET (32 bytes base64)
openssl rand -base64 32
```

**Important**: Keep these values secure and back them up immediately. The ENCRYPTION_KEY cannot be recovered if lost.

## Docker Compose Configuration

Save this as `docker-compose.yml` in your deployment directory:

```yaml
version: "3.8"

services:
  # PostgreSQL database - Required by Infisical
  postgres:
    image: postgres:14-alpine
    container_name: infisical-postgres
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready --username=${POSTGRES_USER} && psql --username=${POSTGRES_USER} --dbname=${POSTGRES_DB} --command 'SELECT 1'"]
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-infisical}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-infisical}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - infisical
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Redis - Required for BullMQ queues
  redis:
    image: redis:7-alpine
    container_name: infisical-redis
    restart: always
    command: redis-server --appendonly yes --appendfsync everysec --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    volumes:
      - redis_data:/data
    networks:
      - infisical
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Infisical backend API server
  infisical:
    image: infisical/infisical:latest  # PIN TO SPECIFIC VERSION IN PRODUCTION: e.g., v0.58.0
    container_name: infisical-server
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "${INFISICAL_PORT:-8080}:8080"
    environment:
      # Core encryption and authentication
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      
      # Database configuration
      DB_CONNECTION_URI: postgres://${POSTGRES_USER:-infisical}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-infisical}
      
      # Redis configuration
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      
      # Required: Site URL - used for redirects, OAuth callbacks, password reset links
      SITE_URL: ${SITE_URL}
      
      # Node environment
      NODE_ENV: production
      
      # Optional: SMTP configuration for email notifications (password reset, invitations, etc.)
      SMTP_HOST: ${SMTP_HOST:-}
      SMTP_PORT: ${SMTP_PORT:-}
      SMTP_USERNAME: ${SMTP_USERNAME:-}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      SMTP_FROM_ADDRESS: ${SMTP_FROM_ADDRESS:-noreply@infisical.local}
      SMTP_FROM_NAME: ${SMTP_FROM_NAME:-Infisical}
      SMTP_REQUIRE_TLS: ${SMTP_REQUIRE_TLS:-true}
      
      # Optional: Monitoring and observability
      SENTRY_DSN: ${SENTRY_DSN:-}
      
      # Optional: Telemetry (set to false if not needed)
      OTEL_TELEMETRY_COLLECTION_ENABLED: ${OTEL_TELEMETRY_COLLECTION_ENABLED:-false}
      OTEL_EXPORT_TYPE: ${OTEL_EXPORT_TYPE:-prometheus}
      
      # Optional: SSO/OAuth configurations (only if using)
      CLIENT_ID_GOOGLE_LOGIN: ${CLIENT_ID_GOOGLE_LOGIN:-}
      CLIENT_SECRET_GOOGLE_LOGIN: ${CLIENT_SECRET_GOOGLE_LOGIN:-}
      CLIENT_ID_GITHUB_LOGIN: ${CLIENT_ID_GITHUB_LOGIN:-}
      CLIENT_SECRET_GITHUB_LOGIN: ${CLIENT_SECRET_GITHUB_LOGIN:-}
      CLIENT_ID_GITLAB_LOGIN: ${CLIENT_ID_GITLAB_LOGIN:-}
      CLIENT_SECRET_GITLAB_LOGIN: ${CLIENT_SECRET_GITLAB_LOGIN:-}
      
      # Optional: FIPS compliance (enterprise/regulated environments)
      FIPS_ENABLED: ${FIPS_ENABLED:-false}
    volumes:
      # Optional: mount logs volume for persistence
      - infisical_logs:/root/.pm2/logs
    networks:
      - infisical
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    # Optional: Resource limits
    # deploy:
    #   resources:
    #     limits:
    #       cpus: '2'
    #       memory: 2G
    #     reservations:
    #       cpus: '1'
    #       memory: 1G

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  infisical_logs:
    driver: local

networks:
  infisical:
    driver: bridge
```

## Environment Variables (.env file)

Create a `.env` file in the same directory with the following values:

```env
# ============================================================================
# CRITICAL: Encryption & Authentication
# ============================================================================
# ENCRYPTION_KEY: 16 bytes (32 hex characters), generated via: openssl rand -hex 16
# This key encrypts all secrets at rest. CANNOT BE RECOVERED IF LOST.
ENCRYPTION_KEY=your_generated_encryption_key_here

# AUTH_SECRET: 32 bytes (base64), generated via: openssl rand -base64 32
# Used for session and JWT signing. Must be stable across restarts.
AUTH_SECRET=your_generated_auth_secret_here

# ============================================================================
# Database Configuration
# ============================================================================
POSTGRES_USER=infisical
POSTGRES_PASSWORD=your_strong_postgres_password_here
POSTGRES_DB=infisical

# ============================================================================
# Redis Configuration
# ============================================================================
REDIS_PASSWORD=your_strong_redis_password_here

# ============================================================================
# Application Configuration
# ============================================================================
# INFISICAL_PORT: Port to expose Infisical on (default: 8080)
INFISICAL_PORT=8080

# SITE_URL: External URL where Infisical is accessible
# Used for OAuth redirects, password reset links, email templates
# Examples: https://infisical.example.com, https://secrets.yourdomain.com
SITE_URL=https://infisical.example.com

# ============================================================================
# SMTP Configuration (Optional - required for email features)
# ============================================================================
# SMTP_HOST: Your mail server hostname
SMTP_HOST=mail.example.com

# SMTP_PORT: SMTP port (typically 587 for TLS, 465 for SSL, 25 for unencrypted)
SMTP_PORT=587

# SMTP_USERNAME: SMTP authentication username
SMTP_USERNAME=noreply@example.com

# SMTP_PASSWORD: SMTP authentication password
SMTP_PASSWORD=your_smtp_password_here

# SMTP_FROM_ADDRESS: Email address for password resets, invitations, etc.
SMTP_FROM_ADDRESS=noreply@example.com

# SMTP_FROM_NAME: Display name in email "From" field
SMTP_FROM_NAME=Infisical Secrets Manager

# SMTP_REQUIRE_TLS: Require TLS for SMTP connection (true/false)
SMTP_REQUIRE_TLS=true

# ============================================================================
# Monitoring (Optional)
# ============================================================================
# SENTRY_DSN: For error tracking and alerting
# Leave empty to disable Sentry
SENTRY_DSN=

# ============================================================================
# Observability (Optional)
# ============================================================================
OTEL_TELEMETRY_COLLECTION_ENABLED=false
OTEL_EXPORT_TYPE=prometheus

# ============================================================================
# SSO/OAuth (Optional - only configure if using)
# ============================================================================
# Google OAuth
CLIENT_ID_GOOGLE_LOGIN=
CLIENT_SECRET_GOOGLE_LOGIN=

# GitHub OAuth
CLIENT_ID_GITHUB_LOGIN=
CLIENT_SECRET_GITHUB_LOGIN=

# GitLab OAuth
CLIENT_ID_GITLAB_LOGIN=
CLIENT_SECRET_GITLAB_LOGIN=

# ============================================================================
# FIPS Compliance (Enterprise)
# ============================================================================
# Set to true to enable FIPS 140-2 compliance
# Requires infisical/infisical:latest-fips image
FIPS_ENABLED=false
```

## Security Best Practices

### 1. Encryption Key Management
- **Generate with cryptographic randomness**: Use `openssl rand -hex 16` for ENCRYPTION_KEY
- **Backup immediately**: Store the key in a secure location (HSM, encrypted vault, secure document)
- **Rotation strategy**: Plan key rotation carefully — rotation requires re-encryption of all secrets
- **Never hardcode**: Always use environment variables or secrets management

### 2. Authentication Secret
- **Generate with randomness**: Use `openssl rand -base64 32` for AUTH_SECRET
- **Stability**: The secret must remain consistent across server restarts
- **Secure storage**: Store in environment variables, not in version control

### 3. Database Security
- **Strong passwords**: Use 20+ character random passwords for PostgreSQL
- **Backup strategy**: Regular automated backups with encryption at rest
- **PostgreSQL version**: Use 14+ (includes important security fixes)
- **Isolated network**: Database accessible only from Infisical service

### 4. Redis Security
- **Password protection**: Set strong Redis password via REDIS_PASSWORD
- **Persistence**: Enabled (appendonly yes) for durability
- **Network isolation**: Redis accessible only from Infisical service
- **Memory limits**: Monitor memory usage; implement eviction policy if needed

### 5. Network & Deployment
- **HTTPS/TLS**: Always use HTTPS in production (set SITE_URL to https://)
- **Reverse proxy**: Deploy behind Nginx/HAProxy with TLS termination
- **IP whitelisting**: Restrict access to Infisical port to known IPs
- **Resource limits**: Set CPU/memory limits to prevent resource exhaustion (see commented section)

### 6. SMTP Configuration
- **Credentials**: Use secure credentials with minimal permissions
- **TLS enforcement**: Set SMTP_REQUIRE_TLS=true in production
- **Testing**: Test email delivery before production deployment

### 7. Logging & Monitoring
- **Log rotation**: JSON-file driver with size limits (10m max-size, 3 max-file)
- **Centralized logging**: Forward logs to ELK, Datadog, or CloudWatch
- **Alerts**: Monitor error rates, database performance, Redis memory
- **Audit logging**: Enable Infisical audit logs in the UI

### 8. Container Hardening
- **Image verification**: Pin to specific version tag (not "latest" in production)
- **Registry**: Use official infisical/infisical repository
- **Read-only filesystem**: Consider adding `read_only: true` with /tmp exemptions (advanced)
- **Non-root user**: Verify Infisical runs as non-root in the image

### 9. Version Pinning
Replace `image: infisical/infisical:latest` with a specific version:
```yaml
image: infisical/infisical:v0.58.0  # Example - replace with your desired version
```

## Deployment Steps

### 1. Initial Setup
```bash
# Create deployment directory
mkdir -p /opt/infisical
cd /opt/infisical

# Copy docker-compose.yml
# Copy .env file (with generated secrets)

# Create required directories with proper permissions
mkdir -p postgres_data redis_data infisical_logs
chmod 700 postgres_data redis_data infisical_logs
```

### 2. Start Services
```bash
# Pull images
docker-compose pull

# Start services (runs migrations automatically on first boot)
docker-compose up -d

# Check logs
docker-compose logs -f infisical

# Verify services are healthy
docker-compose ps
```

### 3. First Access
- Navigate to `https://infisical.example.com` (after HTTPS/reverse proxy setup)
- Create the first admin account
- Log in and change the default settings

### 4. Backup Strategy
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U infisical infisical > backup-$(date +%Y%m%d).sql

# Backup Redis
docker-compose exec redis redis-cli BGSAVE

# Backup encryption key (store securely, NOT with database backups)
cat .env | grep ENCRYPTION_KEY
```

## Reverse Proxy Setup (Nginx)

For production HTTPS deployment:

```nginx
server {
    listen 443 ssl http2;
    server_name infisical.example.com;

    ssl_certificate /etc/letsencrypt/live/infisical.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/infisical.example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
}

server {
    listen 80;
    server_name infisical.example.com;
    return 301 https://$server_name$request_uri;
}
```

## FIPS Compliance (Enterprise)

For regulated environments requiring FIPS 140-2 compliance:

```yaml
# In docker-compose.yml, change the image line:
image: infisical/infisical:latest-fips

# In .env:
FIPS_ENABLED=true
```

FIPS mode uses FIPS-validated cryptographic libraries and disables non-compliant algorithms.

## Monitoring & Health Checks

### Health Check Endpoint
```bash
curl -s http://localhost:8080/api/health | jq
```

### Docker Health Status
```bash
docker-compose ps  # Check STATUS column for (healthy)
docker-compose exec infisical curl -s http://localhost:8080/api/health
```

### Prometheus Metrics (if OTEL enabled)
```bash
curl -s http://localhost:8080/metrics
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running and healthy
docker-compose exec postgres pg_isready -U infisical

# Test connection string
docker-compose exec infisical \
  psql "postgres://infisical:password@postgres:5432/infisical"
```

### Redis Connection Issues
```bash
# Check Redis connectivity
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping
# Should return: PONG
```

### Encryption/Migration Failures
```bash
# View full logs
docker-compose logs infisical | grep -i error

# Check database schema
docker-compose exec postgres psql -U infisical -d infisical \
  -c "\dt"  # List tables
```

### Memory/CPU Issues
```bash
# Monitor resource usage in real-time
docker stats infisical

# Check limits are set correctly
docker-compose config | grep -A 5 resources
```

## Scaling & High Availability

Infisical is stateless and scales horizontally:

1. **Multiple Infisical replicas**: Deploy behind load balancer (Nginx, HAProxy, AWS ALB)
2. **PostgreSQL replication**: Use PostgreSQL streaming replication
3. **Redis Sentinel**: For Redis high availability
4. **Backup restoration**: Regular PostgreSQL backups with point-in-time recovery

Example with multiple Infisical instances:
```yaml
infisical-1:
  image: infisical/infisical:v0.58.0
  # ... same config

infisical-2:
  image: infisical/infisical:v0.58.0
  # ... same config

infisical-3:
  image: infisical/infisical:v0.58.0
  # ... same config
```

Load balance across them with session stickiness disabled (Infisical is stateless).

## Key Takeaways

- **ENCRYPTION_KEY**: 16 bytes (32 hex), generated with openssl, cannot be recovered if lost
- **AUTH_SECRET**: 32 bytes (base64), must be stable across restarts
- **PostgreSQL 14+**: Required with automated backups
- **Redis 6.2+**: Required for BullMQ queues, password-protected
- **SITE_URL**: Must match actual deployment URL (for OAuth, redirects, email links)
- **SMTP**: Optional but needed for password resets and invitations
- **HTTPS**: Always use in production with proper certificate management
- **Monitoring**: Set up logs aggregation and alerts for uptime
- **Backups**: Regular PostgreSQL backups with encryption key backup (separate location)
