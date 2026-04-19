# Docker Deployment Guide

Deploy Infisical using Docker or Docker Compose for flexible, containerized self-hosted environments.

## Docker Standalone Container

### Quick Start

1. Pull the image:
```bash
docker pull infisical/infisical:latest
```

2. Create a `.env` file with required configuration:
```bash
ENCRYPTION_KEY=$(openssl rand -hex 16)
AUTH_SECRET=$(openssl rand -base64 32)
DB_CONNECTION_URI="postgresql://user:password@postgres.example.com:5432/infisical"
REDIS_URL="redis://redis.example.com:6379"
SITE_URL="https://secrets.example.com"
SMTP_HOST="smtp.example.com"
SMTP_PORT="587"
SMTP_USERNAME="user@example.com"
SMTP_PASSWORD="password"
SMTP_FROM_ADDRESS="noreply@example.com"
```

3. Run the container:
```bash
docker run -d \
  --name infisical \
  --env-file .env \
  -p 8080:8080 \
  infisical/infisical:latest
```

4. Verify the container is running:
```bash
curl http://localhost:8080/api/status
```

### Image Variants

#### Standard Image
```bash
docker pull infisical/infisical:latest
docker pull infisical/infisical:v0.110.0  # Specific version
```

#### FIPS 140-2 Compliant Image
Use the FIPS image for regulated environments requiring FIPS compliance:

```bash
docker pull infisical/infisical:latest-fips
```

When using the FIPS image, set:
```bash
FIPS_ENABLED=true
NODE_OPTIONS="--max-old-space-size=8192 --force-fips"
```

## Docker Compose Deployment (Production)

The repository includes `docker-compose.prod.yml` for complete production setups with PostgreSQL and Redis.

### Basic docker-compose.yml

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: infisical-postgres
    environment:
      POSTGRES_USER: infisical
      POSTGRES_PASSWORD: infisical_db_password
      POSTGRES_DB: infisical
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - infisical-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U infisical"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: infisical-redis
    volumes:
      - redis_data:/data
    networks:
      - infisical-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  infisical:
    image: infisical/infisical:latest
    container_name: infisical-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      DB_CONNECTION_URI: postgresql://infisical:infisical_db_password@postgres:5432/infisical
      REDIS_URL: redis://redis:6379
      SITE_URL: https://secrets.example.com
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USERNAME: ${SMTP_USERNAME}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
      SMTP_FROM_ADDRESS: ${SMTP_FROM_ADDRESS}
    ports:
      - "80:8080"
    networks:
      - infisical-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:

networks:
  infisical-network:
    driver: bridge
```

### Configuration

Create a `.env` file in the same directory:

```bash
# Generated keys
ENCRYPTION_KEY=a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8
AUTH_SECRET=VUJrQV9FbmNyeXB0aW9uS2V5XzMyQnl0ZXNfQmFzZTY0RW5jb2RlZA==

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_ADDRESS=noreply@infisical.com
```

### Start the Services

```bash
docker-compose up -d
```

Monitor logs:
```bash
docker-compose logs -f infisical
```

### Upgrade

1. Backup the PostgreSQL database:
```bash
docker-compose exec postgres pg_dump -U infisical infisical > backup.sql
```

2. Pull the new image:
```bash
docker pull infisical/infisical:latest
```

3. Restart the services:
```bash
docker-compose down
docker-compose up -d
```

Schema migrations run automatically on startup.

## External Databases

If using managed PostgreSQL (RDS, Cloud SQL, Azure Database) or managed Redis (ElastiCache, Cloud Memorystore, Azure Cache), configure the connection URIs directly:

```yaml
environment:
  DB_CONNECTION_URI: postgresql://user:password@rds-instance.amazonaws.com:5432/infisical
  DB_ROOT_CERT: ${DB_ROOT_CERT}  # Set if TLS certificate verification is required
  REDIS_URL: rediss://redis-instance.cache.amazonaws.com:6380  # TLS enabled
```

For TLS certificates, base64-encode and pass as `DB_ROOT_CERT`:
```bash
cat /path/to/ca.pem | base64 -w 0 > /tmp/cert.b64
export DB_ROOT_CERT=$(cat /tmp/cert.b64)
```

## Production Hardening

### Read-Only Root Filesystem

Run the container with a read-only root filesystem and temporary writable mounts:

```yaml
infisical:
  image: infisical/infisical:latest
  read_only: true
  tmpfs:
    - /tmp
    - /app/node_modules/.cache
```

This limits the attack surface if the container is compromised.

### Drop Capabilities

Drop unnecessary Linux capabilities:

```yaml
infisical:
  image: infisical/infisical:latest
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE
```

### Resource Limits

Set memory and CPU limits:

```yaml
infisical:
  image: infisical/infisical:latest
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

Adjust based on your expected load.

### Network Security

Restrict network access:

```yaml
networks:
  infisical-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-infisical
```

Use separate networks for different components (application, database, cache).

## Health Checks

The Infisical container exposes a health check endpoint:

```
GET /api/status
```

This returns HTTP 200 if the service is healthy.

### Docker Compose Health Check Configuration

```yaml
infisical:
  image: infisical/infisical:latest
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/api/status"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## Logging

### JSON Logging

Logs are output as JSON for better integration with log aggregation systems:

```bash
docker-compose logs infisical | jq '.msg'
```

### Log File Output

Mount a volume to persist logs:

```yaml
infisical:
  image: infisical/infisical:latest
  volumes:
    - ./logs:/app/logs
  environment:
    LOG_DIR: /app/logs
```

## Networking

### Reverse Proxy (Nginx)

Use Nginx to reverse proxy traffic to Infisical:

```nginx
upstream infisical {
  server infisical:8080;
}

server {
  listen 443 ssl http2;
  server_name secrets.example.com;

  ssl_certificate /etc/letsencrypt/live/secrets.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/secrets.example.com/privkey.pem;

  location / {
    proxy_pass http://infisical;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

In your `.env`, set:
```bash
SITE_URL=https://secrets.example.com
```

### Load Balancing

Deploy multiple Infisical containers behind a load balancer:

```yaml
infisical-1:
  image: infisical/infisical:latest
  environment:
    DB_CONNECTION_URI: postgresql://...
    REDIS_URL: redis://...

infisical-2:
  image: infisical/infisical:latest
  environment:
    DB_CONNECTION_URI: postgresql://...
    REDIS_URL: redis://...

infisical-3:
  image: infisical/infisical:latest
  environment:
    DB_CONNECTION_URI: postgresql://...
    REDIS_URL: redis://...

loadbalancer:
  image: nginx:latest
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
```

All instances share the same PostgreSQL and Redis, making the service stateless and scalable.

## Backup and Recovery

### Backup PostgreSQL

```bash
docker-compose exec postgres pg_dump -U infisical infisical > backup_$(date +%s).sql
```

### Restore PostgreSQL

```bash
docker-compose exec -T postgres psql -U infisical infisical < backup.sql
```

### Backup Redis

```bash
docker-compose exec redis redis-cli BGSAVE
docker cp infisical-redis:/data/dump.rdb ./redis_backup.rdb
```

Always backup before upgrading or making configuration changes.
