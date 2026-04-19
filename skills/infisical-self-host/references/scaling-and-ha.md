# Scaling and High Availability Guide

Infisical is a stateless application designed to scale horizontally. This guide covers scaling patterns, sizing recommendations, high availability (HA) setup, and upgrade procedures.

## Architecture Overview

Infisical's stateless architecture means:

- **All state is external**: PostgreSQL stores data, Redis handles caching and job queues
- **Horizontal scaling**: Add more Infisical replicas without reconfiguration
- **Load balancing**: Multiple replicas distribute traffic evenly
- **Zero shared state**: Each replica is identical and independent

This enables seamless scaling from single-node deployments to large distributed clusters.

## Sizing Recommendations

Choose deployment sizes based on your organization's users, secrets, and API request volume.

### Small Deployment

**Use Case**: Development, testing, small organizations (< 50 users)

**Infisical**:
- Replicas: 2
- CPU: 2 cores per replica
- Memory: 4-8 GB per replica
- Storage: N/A (stateless)

**PostgreSQL**:
- vCPU: 2
- Memory: 8 GB
- Storage: 100 GB (SSD recommended)
- Configuration: Single instance with automated backups

**Redis**:
- vCPU: 2
- Memory: 4 GB
- Storage: N/A (in-memory)
- Configuration: Standalone (simplest for this size)

### Medium Deployment

**Use Case**: Production environments (50-500 users)

**Infisical**:
- Replicas: 5
- CPU: 2-4 cores per replica
- Memory: 4-8 GB per replica
- Storage: N/A (stateless)

**PostgreSQL**:
- vCPU: 4
- Memory: 16 GB
- Storage: 200 GB (SSD)
- Configuration: Primary + read replicas for load distribution

**Redis**:
- vCPU: 2
- Memory: 4 GB
- Configuration: Standalone or Sentinel for HA

### Large Deployment

**Use Case**: Enterprise environments (500+ users)

**Infisical**:
- Replicas: 10+
- CPU: 2-4 cores per replica
- Memory: 4-8 GB per replica
- Storage: N/A (stateless)

**PostgreSQL**:
- vCPU: 8
- Memory: 32 GB
- Storage: 500 GB+ (SSD with RAID)
- Configuration: Primary + multiple read replicas, automated backups and WAL archiving

**Redis**:
- vCPU: 2-4
- Memory: 4-8 GB
- Configuration: Redis Sentinel for HA or Redis Cluster (but Infisical does NOT support Cluster mode)

## Horizontal Scaling

### Docker Compose

To scale Infisical with Docker Compose, create multiple service definitions:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: infisical
      POSTGRES_PASSWORD: password
      POSTGRES_DB: infisical
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  infisical-1:
    image: infisical/infisical:latest
    depends_on:
      - postgres
      - redis
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      DB_CONNECTION_URI: postgresql://infisical:password@postgres:5432/infisical
      REDIS_URL: redis://redis:6379
      SITE_URL: https://secrets.example.com
    ports:
      - "8001:8080"

  infisical-2:
    image: infisical/infisical:latest
    depends_on:
      - postgres
      - redis
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      DB_CONNECTION_URI: postgresql://infisical:password@postgres:5432/infisical
      REDIS_URL: redis://redis:6379
      SITE_URL: https://secrets.example.com
    ports:
      - "8002:8080"

  infisical-3:
    image: infisical/infisical:latest
    depends_on:
      - postgres
      - redis
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      AUTH_SECRET: ${AUTH_SECRET}
      DB_CONNECTION_URI: postgresql://infisical:password@postgres:5432/infisical
      REDIS_URL: redis://redis:6379
      SITE_URL: https://secrets.example.com
    ports:
      - "8003:8080"

  nginx:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - infisical-1
      - infisical-2
      - infisical-3

volumes:
  postgres_data:
  redis_data:
```

Use Nginx or HAProxy as a load balancer to distribute traffic:

```nginx
upstream infisical {
  server infisical-1:8080;
  server infisical-2:8080;
  server infisical-3:8080;
}

server {
  listen 80;
  location / {
    proxy_pass http://infisical;
  }
}
```

### Kubernetes

Scale using kubectl:

```bash
kubectl scale deployment infisical --replicas=10 -n infisical
```

Or update the Helm values:

```yaml
replicaCount: 10
```

Then apply:

```bash
helm upgrade infisical infisical/infisical-standalone-postgres \
  --namespace infisical \
  -f values.yaml
```

## Database Replication

### PostgreSQL Read Replicas

For large deployments, use PostgreSQL read replicas to distribute read-heavy queries (secrets, audit logs):

```bash
DB_READ_REPLICAS='[
  {"connectionString": "postgresql://user:pass@replica1.amazonaws.com:5432/infisical"},
  {"connectionString": "postgresql://user:pass@replica2.amazonaws.com:5432/infisical"}
]'
```

Infisical will distribute SELECT queries across replicas while ensuring writes go to the primary.

### Setting Up AWS RDS Read Replicas

1. Create a read replica in AWS RDS:
```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier infisical-replica-1 \
  --source-db-instance-identifier infisical-primary
```

2. Configure in Infisical:
```bash
DB_READ_REPLICAS='[
  {"connectionString": "postgresql://user:password@infisical-replica-1.123456789.us-east-1.rds.amazonaws.com:5432/infisical"}
]'
```

## Redis High Availability

Infisical supports Redis Sentinel for high availability. Cluster mode is NOT supported.

### Redis Sentinel Setup

Sentinel monitors Redis and automatically promotes a replica to master if the primary fails.

#### Configure Sentinel

Create `sentinel.conf`:

```
port 26379
sentinel monitor mymaster 192.168.1.100 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000
```

Run three Sentinel nodes for quorum:

```bash
redis-sentinel sentinel-1.conf
redis-sentinel sentinel-2.conf
redis-sentinel sentinel-3.conf
```

#### Configure Infisical to Use Sentinel

```bash
REDIS_SENTINEL_HOSTS="sentinel1.example.com:26379,sentinel2.example.com:26379,sentinel3.example.com:26379"
REDIS_SENTINEL_MASTER_NAME="mymaster"
REDIS_SENTINEL_ENABLE_TLS="true"
REDIS_SENTINEL_USERNAME="sentinel-user"
REDIS_SENTINEL_PASSWORD="sentinel-password"
```

Infisical will discover the current Redis master through Sentinel and automatically handle failovers.

### Docker Compose with Sentinel

```yaml
redis-master:
  image: redis:7-alpine
  ports:
    - "6379:6379"

redis-replica:
  image: redis:7-alpine
  command: redis-server --slaveof redis-master 6379
  depends_on:
    - redis-master

sentinel-1:
  image: redis:7-alpine
  command: redis-sentinel /sentinel.conf
  volumes:
    - ./sentinel.conf:/sentinel.conf
  ports:
    - "26379:26379"

sentinel-2:
  image: redis:7-alpine
  command: redis-sentinel /sentinel.conf
  volumes:
    - ./sentinel.conf:/sentinel.conf
  ports:
    - "26380:26379"

sentinel-3:
  image: redis:7-alpine
  command: redis-sentinel /sentinel.conf
  volumes:
    - ./sentinel.conf:/sentinel.conf
  ports:
    - "26381:26379"

infisical:
  image: infisical/infisical:latest
  environment:
    REDIS_SENTINEL_HOSTS: "sentinel-1:26379,sentinel-2:26379,sentinel-3:26379"
    REDIS_SENTINEL_MASTER_NAME: "mymaster"
```

## Backup and Disaster Recovery

### PostgreSQL Backup Strategy

**Automated Backups**:

For managed PostgreSQL (RDS, Cloud SQL), use automated backups:

```bash
# AWS RDS
aws rds create-db-snapshot \
  --db-instance-identifier infisical \
  --db-snapshot-identifier infisical-backup-$(date +%s)
```

**Manual Backups**:

For self-hosted PostgreSQL:

```bash
pg_dump -h pg.example.com -U infisical infisical | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Point-in-Time Recovery** (if WAL archiving is configured):

```bash
# Configure WAL archiving in PostgreSQL postgresql.conf
archive_mode = on
archive_command = 'aws s3 cp %p s3://backup-bucket/wal_archive/%f'
```

Then restore to a specific point in time.

### Redis Backup

Redis backups are less critical than database backups (data can be repopulated from PostgreSQL), but they can speed up recovery:

```bash
redis-cli BGSAVE
redis-cli LASTSAVE  # Shows timestamp of last snapshot
```

Backup the RDB file periodically:

```bash
cp /var/lib/redis/dump.rdb /backup/redis_$(date +%s).rdb
```

### Backup Schedule

- **PostgreSQL**: Daily automated backups + continuous WAL archiving
- **Redis**: Daily snapshots (optional, less critical)
- **Retention**: Keep at least 30 days of backups for compliance

### Test Restores

Regularly test restores in a non-production environment to ensure backup integrity.

## Upgrades

Upgrading Infisical with zero downtime:

1. **Backup the database** (critical):
```bash
pg_dump -h pg.example.com -U infisical infisical > backup.sql
```

2. **Check the upgrade path** (optional):
Visit https://app.infisical.com/upgrade-path to verify your upgrade path and any special steps.

3. **Update replicas incrementally**:

   For Kubernetes with rolling updates:
   ```bash
   kubectl set image deployment/infisical infisical=infisical/infisical:new-version -n infisical
   ```

   The rolling update ensures some replicas stay running while others update.

4. **Monitor the rollout**:
   ```bash
   kubectl rollout status deployment/infisical -n infisical
   ```

5. **Schema migrations run automatically** on startup (since v0.111.0-postgres):
   - One instance acquires a lock
   - Migrations run
   - Other instances wait for migrations to complete
   - Cluster is ready

6. **Rollback if needed**:
   ```bash
   kubectl rollout undo deployment/infisical -n infisical
   ```

## Licensing and Compliance

### License Server IP Addresses

Enterprise Infisical installations require connectivity to the license server. Whitelist these IPs in your firewall:

- `13.248.249.247`
- `35.71.190.59`

Ensure outbound HTTPS (port 443) is allowed to these addresses.

## Monitoring and Observability

### Key Metrics to Monitor

- **CPU and Memory**: Per-replica resource utilization
- **Request Latency**: API response times
- **Error Rate**: 5xx errors, database connection errors
- **Database Connections**: Active connections, connection pool saturation
- **Redis Memory**: Memory usage and eviction
- **Database Query Time**: Slow query logs

### Prometheus Metrics

Infisical exposes metrics on `/metrics` (OpenTelemetry format):

```bash
curl http://infisical:8080/metrics
```

### Log Aggregation

Aggregate logs from all replicas using your logging platform:

```bash
# Docker Compose
docker-compose logs infisical | grep ERROR

# Kubernetes
kubectl logs -l app=infisical -n infisical --all-containers=true
```

## Performance Tuning

### PostgreSQL Tuning

For large deployments, optimize PostgreSQL:

```sql
-- Increase shared buffers (typically 25% of RAM)
ALTER SYSTEM SET shared_buffers = '8GB';

-- Increase effective cache size (typically 50-75% of RAM)
ALTER SYSTEM SET effective_cache_size = '24GB';

-- Increase work_mem for complex queries
ALTER SYSTEM SET work_mem = '8MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Tuning

Increase maxmemory if needed:

```bash
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Connection Pool Tuning

Monitor connection pool saturation and adjust if needed:

```bash
# Check PostgreSQL max connections
psql -h pg.example.com -U infisical -d infisical -c "SHOW max_connections;"
```

Increase if you have many Infisical replicas:

```bash
ALTER SYSTEM SET max_connections = 400;
```

## Troubleshooting HA Setups

### Redis Sentinel Failover Not Triggering

Check Sentinel logs:

```bash
redis-cli -p 26379 SENTINEL MASTERS
redis-cli -p 26379 SENTINEL SLAVES mymaster
```

Ensure Sentinel nodes can communicate with Redis.

### Database Connection Pool Exhaustion

If you see "too many connections" errors:

1. Check current connections:
```bash
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

2. Increase PostgreSQL max_connections
3. Reduce Infisical replicas or increase connection pool size

### Read Replica Lag

If read replicas are lagging, monitor replication lag:

```bash
# AWS RDS
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,ReplicationLag]'
```

Lag > 1 second may cause stale reads. Infisical writes always use the primary.

## Capacity Planning

To estimate hardware needs:

- **Users**: 10 users per core for moderate activity
- **Secrets**: 1 million secrets per 10 GB of PostgreSQL storage
- **API Calls**: 1000 req/sec per 2 cores with 4 GB memory
- **Database Connections**: 20-50 per Infisical replica

Example for 200 users:
- Infisical: 3 replicas x 2 cores
- PostgreSQL: 4 vCPU, 16 GB RAM, 100 GB storage
- Redis: 2 vCPU, 4 GB RAM

Adjust based on actual monitoring and load testing.
