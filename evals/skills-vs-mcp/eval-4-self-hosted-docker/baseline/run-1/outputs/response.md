# Production-Ready Docker Compose for Self-Hosted Infisical

This document provides a complete, production-ready `docker-compose.yml` for self-hosting Infisical with proper encryption, security hardening, and all required configuration.

## docker-compose.yml

```yaml
version: "3.9"

services:
  # Reverse proxy with TLS termination
  nginx:
    image: nginx:1.27-alpine
    container_name: infisical-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl/infisical.crt:/etc/nginx/ssl/infisical.crt:ro
      - ./ssl/infisical.key:/etc/nginx/ssl/infisical.key:ro
    depends_on:
      - backend
      - frontend
    networks:
      - infisical
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      com.example.description: "Reverse proxy and TLS termination"

  # PostgreSQL database with persistence
  db:
    image: postgres:15-alpine
    container_name: infisical-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-infisical}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Database password required}
      POSTGRES_DB: ${POSTGRES_DB:-infisical}
      POSTGRES_INITDB_ARGS: "-c max_connections=200 -c shared_buffers=256MB -c effective_cache_size=1GB"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./postgres-init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - infisical
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-infisical} -d ${POSTGRES_DB:-infisical}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    labels:
      com.example.description: "PostgreSQL database for Infisical"

  # Redis for queues and caching
  redis:
    image: redis:7-alpine
    container_name: infisical-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD:?Redis password required} --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - infisical
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    labels:
      com.example.description: "Redis for queues and caching"

  # Infisical Backend API
  backend:
    image: infisical/infisical:${INFISICAL_VERSION:-latest}
    container_name: infisical-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      # Core Configuration
      NODE_ENV: production
      
      # Database
      DB_CONNECTION_URI: postgres://${POSTGRES_USER:-infisical}:${POSTGRES_PASSWORD:?Database password required}@db:5432/${POSTGRES_DB:-infisical}?sslmode=disable
      
      # Redis
      REDIS_URL: redis://:${REDIS_PASSWORD:?Redis password required}@redis:6379
      
      # Encryption Keys (MUST be strong 32-character hex strings)
      ENCRYPTION_KEY: ${ENCRYPTION_KEY:?32-character encryption key required}
      
      # JWT/Auth Secrets (MUST be strong base64-encoded strings, minimum 32 bytes)
      AUTH_SECRET: ${AUTH_SECRET:?Base64-encoded auth secret required}
      
      # Site Configuration
      SITE_URL: ${SITE_URL:-https://infisical.example.com}
      
      # SMTP Email Configuration (optional but recommended)
      SMTP_HOST: ${SMTP_HOST:-}
      SMTP_PORT: ${SMTP_PORT:-587}
      SMTP_FROM_ADDRESS: ${SMTP_FROM_ADDRESS:-noreply@infisical.example.com}
      SMTP_FROM_NAME: ${SMTP_FROM_NAME:-Infisical}
      SMTP_USERNAME: ${SMTP_USERNAME:-}
      SMTP_PASSWORD: ${SMTP_PASSWORD:-}
      SMTP_TLS: "true"
      
      # Logging & Telemetry
      LOG_LEVEL: ${LOG_LEVEL:-info}
      OTEL_TELEMETRY_COLLECTION_ENABLED: ${OTEL_TELEMETRY_COLLECTION_ENABLED:-false}
      TELEMETRY_ENABLED: ${TELEMETRY_ENABLED:-false}
      
      # ClickHouse (optional) for audit logs
      # CLICKHOUSE_URL: http://infisical:${CLICKHOUSE_PASSWORD}@clickhouse:8123/infisical
      
      # SSO (optional)
      CLIENT_ID_GOOGLE_LOGIN: ${CLIENT_ID_GOOGLE_LOGIN:-}
      CLIENT_SECRET_GOOGLE_LOGIN: ${CLIENT_SECRET_GOOGLE_LOGIN:-}
      CLIENT_ID_GITHUB_LOGIN: ${CLIENT_ID_GITHUB_LOGIN:-}
      CLIENT_SECRET_GITHUB_LOGIN: ${CLIENT_SECRET_GITHUB_LOGIN:-}
      
      # Rate Limiting
      MAX_REQUESTS_PER_SECOND: ${MAX_REQUESTS_PER_SECOND:-100}
      
      # HTTPS/SSL
      ACCEPT_INSECURE_CA: "false"
      
      # API Key Settings
      PLAIN_API_KEY: ${PLAIN_API_KEY:-}
    volumes:
      - backend_logs:/app/logs
    networks:
      - infisical
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      com.example.description: "Infisical backend API server"

  # Infisical Frontend (served by backend in standalone mode, but can be separate)
  frontend:
    image: infisical/infisical:${INFISICAL_VERSION:-latest}
    container_name: infisical-frontend
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      NODE_ENV: production
      VITE_API_URL: ${SITE_URL:-https://infisical.example.com}/api
    networks:
      - infisical
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    labels:
      com.example.description: "Infisical frontend"
    # Note: In the standalone image, frontend is usually built into backend
    # If using separate frontend, adjust accordingly

volumes:
  pg_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/redis
  backend_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/logs

networks:
  infisical:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Environment File (.env)

Create a `.env` file in the same directory with these required and recommended variables:

```bash
# ==================== REQUIRED ====================

# PostgreSQL Configuration
POSTGRES_USER=infisical_prod
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD_32_CHARS>
POSTGRES_DB=infisical_prod

# Redis Configuration
REDIS_PASSWORD=<GENERATE_STRONG_PASSWORD_32_CHARS>

# Encryption Keys (CRITICAL: Generate these securely)
# Generate with: openssl rand -hex 16
ENCRYPTION_KEY=<GENERATE_32_CHAR_HEX_STRING>

# JWT Auth Secret (CRITICAL: Generate this securely)
# Generate with: openssl rand -base64 32
AUTH_SECRET=<GENERATE_BASE64_ENCODED_STRING_32_BYTES>

# Site URL (change to your domain)
SITE_URL=https://infisical.example.com

# ==================== RECOMMENDED ====================

# SMTP Configuration (for password resets, invitations)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_ADDRESS=noreply@infisical.example.com
SMTP_FROM_NAME=Infisical
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password

# Logging
LOG_LEVEL=info
TELEMETRY_ENABLED=false
OTEL_TELEMETRY_COLLECTION_ENABLED=false

# Infisical Version (pin to specific version for stability)
INFISICAL_VERSION=v0.XX.X

# Data Directory (for persistent volumes)
DATA_DIR=./data

# ==================== OPTIONAL ====================

# SSO Integration
CLIENT_ID_GOOGLE_LOGIN=
CLIENT_SECRET_GOOGLE_LOGIN=

CLIENT_ID_GITHUB_LOGIN=
CLIENT_SECRET_GITHUB_LOGIN=

# Rate Limiting
MAX_REQUESTS_PER_SECOND=100

# ClickHouse (optional, for audit logs)
CLICKHOUSE_PASSWORD=

# API Key Setting
PLAIN_API_KEY=
```

## Nginx Configuration (nginx.conf)

Create an `nginx.conf` file for reverse proxy and TLS termination:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

    # Upstream backend
    upstream infisical_backend {
        server backend:8080 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name infisical.example.com;

        # TLS Configuration
        ssl_certificate /etc/nginx/ssl/infisical.crt;
        ssl_certificate_key /etc/nginx/ssl/infisical.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css text/xml text/javascript 
                   application/x-javascript application/xml+rss 
                   application/javascript application/json;
        gzip_min_length 1024;
        gzip_vary on;

        # Backend proxy
        location /api {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://infisical_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login_limit burst=5 nodelay;
            
            proxy_pass http://infisical_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://infisical_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            access_log off;
        }

        # Frontend
        location / {
            proxy_pass http://infisical_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
```

## PostgreSQL Initialization Script (postgres-init.sql)

Create `postgres-init.sql` to set up database security:

```sql
-- PostgreSQL initialization script for Infisical

-- Set password encryption
ALTER USER infisical_prod WITH ENCRYPTED PASSWORD 'will-be-overridden-by-env';

-- Configure connection limits
ALTER DATABASE infisical_prod SET max_connections = 200;

-- Enable SSL if needed (set in postgresql.conf via environment)
-- ALTER SYSTEM SET ssl = on;

-- Create required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO infisical_prod;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO infisical_prod;

-- Revoke public schema permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Grant infisical user access
GRANT USAGE ON SCHEMA public TO infisical_prod;
GRANT CREATE ON SCHEMA public TO infisical_prod;
```

## Security Deployment Steps

### 1. Generate Required Secrets

```bash
# Generate encryption key (32 hex characters)
ENCRYPTION_KEY=$(openssl rand -hex 16)
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"

# Generate auth secret (base64-encoded, 32+ bytes)
AUTH_SECRET=$(openssl rand -base64 32)
echo "AUTH_SECRET=$AUTH_SECRET"

# Generate database password
DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+" | cut -c1-24)
echo "POSTGRES_PASSWORD=$DB_PASSWORD"

# Generate Redis password
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+" | cut -c1-24)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
```

### 2. SSL/TLS Certificates

For production, use Let's Encrypt:

```bash
# Create SSL directory
mkdir -p ssl

# Using certbot with standalone mode
certbot certonly --standalone \
  -d infisical.example.com \
  -d www.infisical.example.com \
  --email admin@example.com \
  --agree-tos

# Copy certificates to nginx directory
cp /etc/letsencrypt/live/infisical.example.com/fullchain.pem ssl/infisical.crt
cp /etc/letsencrypt/live/infisical.example.com/privkey.pem ssl/infisical.key

# Fix permissions
chmod 644 ssl/infisical.crt
chmod 600 ssl/infisical.key
```

For self-signed (development only):

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/infisical.key \
  -out ssl/infisical.crt \
  -subj "/CN=infisical.example.com"
```

### 3. Directory Structure

```
infisical-deployment/
├── docker-compose.yml
├── .env (keep secure - do NOT commit)
├── nginx.conf
├── postgres-init.sql
├── data/
│   ├── postgres/     (PostgreSQL data)
│   ├── redis/        (Redis data)
│   └── logs/         (Application logs)
└── ssl/
    ├── infisical.crt (certificate)
    └── infisical.key (private key - keep secure)
```

### 4. Pre-deployment Checklist

- [ ] Generate strong encryption and auth secrets
- [ ] Create `.env` file with all required variables
- [ ] Obtain valid SSL certificates
- [ ] Update domain in `SITE_URL` and nginx config
- [ ] Configure SMTP for email notifications
- [ ] Create `data/` directories with proper permissions
- [ ] Review security headers in nginx config
- [ ] Set file permissions: `chmod 600 .env && chmod 600 ssl/infisical.key`
- [ ] Test database connectivity before production
- [ ] Enable automated backups for `data/postgres/`
- [ ] Set up log rotation for application logs

### 5. Start the Deployment

```bash
# Create data directories
mkdir -p data/{postgres,redis,logs}
chmod 700 data

# Validate compose file
docker-compose config

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

### 6. Verify Installation

```bash
# Check if Infisical is running
curl -k https://infisical.example.com/health

# Check service logs
docker-compose logs backend
docker-compose logs db
docker-compose logs redis

# Run database migrations (if needed)
docker-compose exec backend npm run migration:latest
```

## Security Best Practices

### Encryption & Keys

1. **ENCRYPTION_KEY**: Used for encrypting/decrypting secrets. Generate with `openssl rand -hex 16`.
2. **AUTH_SECRET**: Used for JWT signing. Generate with `openssl rand -base64 32`.
3. Store secrets in `.env` file with restricted permissions (`chmod 600`).
4. Never commit `.env` to version control.
5. Rotate keys periodically (requires re-encryption of existing secrets).

### Network Security

- Backend and database communicate only over internal network.
- Nginx provides TLS termination and rate limiting.
- Network is isolated from host (no exposed ports except 80/443).
- PostgreSQL port not exposed to external network.
- Redis requires authentication with password.

### Database Security

- PostgreSQL runs with non-root user.
- Database has limited privileges and connection limits.
- Passwords are strong and randomly generated.
- Connection string uses standard security settings.
- Extensions (`uuid-ossp`, `pgcrypto`) enabled for encryption support.

### Container Security

- Containers run with `no-new-privileges:true`.
- Unnecessary capabilities dropped (`cap_drop: ALL`).
- Only required capabilities added (`NET_BIND_SERVICE`).
- Images pulled from official registries.
- Version pinning recommended to avoid unexpected updates.

### Production Monitoring

Add monitoring with Prometheus/Grafana:

```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
```

## Backup & Recovery

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U infisical_prod infisical_prod > backup.sql

# Backup Redis
docker-compose exec redis redis-cli --rdb /tmp/dump.rdb
docker cp infisical-redis:/tmp/dump.rdb ./redis-backup.rdb

# Backup entire data directory
tar -czf infisical-backup-$(date +%Y%m%d).tar.gz data/

# Restore PostgreSQL
docker-compose exec -T db psql -U infisical_prod infisical_prod < backup.sql
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container fails to start | Check logs: `docker-compose logs <service>` |
| Database connection errors | Verify `DB_CONNECTION_URI` and wait for DB health check |
| SSL certificate errors | Ensure certificate paths in nginx.conf are correct |
| High memory usage | Adjust Redis `maxmemory` and PostgreSQL `shared_buffers` |
| Rate limiting too strict | Adjust `limit_req_zone` rate in nginx.conf |
| Secrets encrypted with old key | Store new key in `ENCRYPTION_KEY`, re-encrypt via UI |

## References

- [Infisical Self-Hosted Docs](https://infisical.com/docs/self-hosting/overview)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/sql-syntax.html)
- [Redis Security](https://redis.io/docs/management/security/)
- [Nginx Security](https://nginx.org/en/docs/)
