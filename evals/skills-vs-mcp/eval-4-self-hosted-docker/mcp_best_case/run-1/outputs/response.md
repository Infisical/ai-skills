# Production-Ready Infisical Self-Hosted Docker Compose Setup

Here's a complete, production-ready `docker-compose.yml` for self-hosting Infisical with proper security and encryption:

## docker-compose.prod.yml

```yaml
version: '3.8'

services:
  infisical-backend:
    image: infisical/infisical:latest
    container_name: infisical-backend
    ports:
      - "80:8080"
    depends_on:
      - infisical-db
      - infisical-redis
    environment:
      # === REQUIRED: Encryption & Security ===
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      SITE_URL: ${SITE_URL}
      
      # === DATABASE ===
      DB_CONNECTION_URI: ${DB_CONNECTION_URI}
      
      # === CACHING & BACKGROUND JOBS ===
      REDIS_URL: ${REDIS_URL}
      
      # === OPTIONAL: Telemetry ===
      TELEMETRY_ENABLED: ${TELEMETRY_ENABLED:-false}
      
      # === OPTIONAL: Application Port ===
      PORT: ${PORT:-8080}
      
      # === OPTIONAL: Frontend Configuration ===
      # NODE_ENV: production
      # LOG_LEVEL: info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - infisical-network
    volumes:
      - infisical-data:/data

  infisical-db:
    image: postgres:16-alpine
    container_name: infisical-db
    environment:
      POSTGRES_USER: ${DB_USER:-infisical}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-infisical}
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-infisical}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - infisical-network
    volumes:
      - postgres-data:/var/lib/postgresql/data
    # Security: limit resources
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  infisical-redis:
    image: redis:7-alpine
    container_name: infisical-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - infisical-network
    volumes:
      - redis-data:/data
    # Security: limit resources
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

networks:
  infisical-network:
    driver: bridge

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  infisical-data:
    driver: local
```

## .env Configuration File

Create a `.env` file in the same directory as your `docker-compose.prod.yml`:

```bash
# ============================================
# REQUIRED: Encryption & Security
# ============================================

# Generate with: openssl rand -hex 16
ENCRYPTION_KEY=your_16_byte_hex_string_here

# Generate with: openssl rand -base64 32
AUTH_SECRET=your_32_byte_base64_string_here

# Must be an absolute URL with protocol
SITE_URL=https://infisical.yourdomain.com

# ============================================
# REQUIRED: Database Configuration
# ============================================

DB_USER=infisical
DB_PASSWORD=your_secure_db_password_here
DB_NAME=infisical

# PostgreSQL connection string (internal Docker hostname)
DB_CONNECTION_URI=postgresql://infisical:your_secure_db_password_here@infisical-db:5432/infisical

# ============================================
# REQUIRED: Redis Configuration
# ============================================

REDIS_PASSWORD=your_secure_redis_password_here

# Redis connection string (internal Docker hostname)
REDIS_URL=redis://:your_secure_redis_password_here@infisical-redis:6379

# ============================================
# OPTIONAL: Application Settings
# ============================================

PORT=8080
TELEMETRY_ENABLED=false
# NODE_ENV=production
# LOG_LEVEL=info
```

## Setup Instructions

### 1. Generate Secure Credentials

```bash
# Generate ENCRYPTION_KEY (16-byte hex)
ENCRYPTION_KEY=$(openssl rand -hex 16)
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"

# Generate AUTH_SECRET (32-byte base64)
AUTH_SECRET=$(openssl rand -base64 32)
echo "AUTH_SECRET=$AUTH_SECRET"

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)
echo "DB_PASSWORD=$DB_PASSWORD"

# Generate Redis password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
```

### 2. Create Environment File

```bash
cat > .env << EOF
ENCRYPTION_KEY=$ENCRYPTION_KEY
AUTH_SECRET=$AUTH_SECRET
SITE_URL=https://infisical.yourdomain.com

DB_USER=infisical
DB_PASSWORD=$DB_PASSWORD
DB_NAME=infisical
DB_CONNECTION_URI=postgresql://infisical:$DB_PASSWORD@infisical-db:5432/infisical

REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@infisical-redis:6379

PORT=8080
TELEMETRY_ENABLED=false
EOF
```

### 3. Start the Stack

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f infisical-backend

# Test health check
curl http://localhost/health
```

## Production Hardening Recommendations

1. **SSL/TLS Termination**: Use Nginx or Caddy as a reverse proxy:
   - Terminate SSL/TLS at the proxy layer
   - Forward traffic to the backend on port 8080
   - Implement security headers (HSTS, CSP, etc.)

2. **Database Backups**: Schedule regular PostgreSQL backups:
   ```bash
   docker exec infisical-db pg_dump -U infisical infisical > backup.sql
   ```

3. **Monitoring & Logging**: 
   - Monitor container health and resource usage
   - Collect logs centrally
   - Set up alerts for failures

4. **Network Security**:
   - Isolate the Docker network from external access
   - Use strong passwords for all services
   - Rotate credentials regularly

5. **Environment Variables**:
   - Store `.env` in a secure location
   - Use encrypted configuration management for production
   - Never commit `.env` to version control

6. **Resource Limits**:
   - The compose file includes CPU and memory limits
   - Adjust based on your expected load
   - Monitor actual usage and scale as needed

## Disaster Recovery

### Database Backup
```bash
docker exec infisical-db pg_dump -U infisical -Fc infisical > infisical_$(date +%Y%m%d_%H%M%S).backup
```

### Database Restore
```bash
docker exec -i infisical-db pg_restore -U infisical -d infisical < infisical_backup.backup
```

### Complete Stack Migration
Keep encrypted `.env` and database backups in secure, offsite storage for disaster recovery.

## Security Checklist

- [ ] ENCRYPTION_KEY generated with `openssl rand -hex 16`
- [ ] AUTH_SECRET generated with `openssl rand -base64 32`
- [ ] SITE_URL configured with HTTPS protocol
- [ ] Database password changed from default
- [ ] Redis password set and secured
- [ ] `.env` file not committed to version control
- [ ] SSL/TLS reverse proxy configured
- [ ] Database backups scheduled
- [ ] Monitoring and alerting configured
- [ ] Network isolation verified
- [ ] TELEMETRY_ENABLED disabled (unless desired)
