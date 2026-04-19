# Kubernetes Deployment Guide

Deploy Infisical on Kubernetes using the official Helm chart for scalable, cloud-native deployments.

## Prerequisites

- Kubernetes 1.23 or newer
- Helm 3.11.3 or newer
- `kubectl` configured and authenticated to your cluster
- PostgreSQL 14+ (managed or in-cluster)
- Redis 6.2+ (managed or in-cluster)

## Helm Chart Installation

### Add the Infisical Helm Repository

```bash
helm repo add infisical https://dl.cloudsmith.io/public/infisical/helm-charts/helm/charts/
helm repo update
```

### Create a Namespace

```bash
kubectl create namespace infisical
```

### Create Secrets

Before installing the chart, create a Kubernetes secret with required environment variables:

```bash
kubectl create secret generic infisical-secrets \
  --from-literal=ENCRYPTION_KEY=$(openssl rand -hex 16) \
  --from-literal=AUTH_SECRET=$(openssl rand -base64 32) \
  --from-literal=DB_CONNECTION_URI="postgresql://user:password@postgres-host:5432/infisical" \
  --from-literal=REDIS_URL="redis://redis-host:6379" \
  --from-literal=SITE_URL="https://secrets.example.com" \
  --from-literal=SMTP_HOST="smtp.example.com" \
  --from-literal=SMTP_PORT="587" \
  --from-literal=SMTP_USERNAME="user@example.com" \
  --from-literal=SMTP_PASSWORD="password" \
  --from-literal=SMTP_FROM_ADDRESS="noreply@infisical.com" \
  -n infisical
```

### Install the Chart

```bash
helm install infisical infisical/infisical-standalone-postgres \
  --namespace infisical \
  --values values.yaml
```

## Values Configuration

Create a `values.yaml` file to customize the deployment:

```yaml
# Replica count for horizontal scaling
replicaCount: 3

image:
  repository: infisical/infisical
  tag: latest
  pullPolicy: IfNotPresent

# Pod configuration
podAnnotations: {}
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1001
  fsGroup: 1001

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true

# Resource limits
resources:
  limits:
    cpu: 2
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

# Service
service:
  type: ClusterIP
  port: 8080

# Environment variables from the secret
env:
  - name: ENCRYPTION_KEY
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: ENCRYPTION_KEY
  - name: AUTH_SECRET
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: AUTH_SECRET
  - name: DB_CONNECTION_URI
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: DB_CONNECTION_URI
  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: REDIS_URL
  - name: SITE_URL
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SITE_URL
  - name: SMTP_HOST
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SMTP_HOST
  - name: SMTP_PORT
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SMTP_PORT
  - name: SMTP_USERNAME
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SMTP_USERNAME
  - name: SMTP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SMTP_PASSWORD
  - name: SMTP_FROM_ADDRESS
    valueFrom:
      secretKeyRef:
        name: infisical-secrets
        key: SMTP_FROM_ADDRESS

# Persistence (for temporary files)
persistence:
  enabled: true
  storageClassName: standard
  accessMode: ReadWriteOnce
  size: 2Gi
  mountPath: /tmp

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: secrets.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: infisical-tls
      hosts:
        - secrets.example.com

# Health checks
livenessProbe:
  httpGet:
    path: /api/status
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/status
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5

# PostgreSQL (optional - if using in-cluster)
postgresql:
  enabled: true
  auth:
    username: infisical
    password: change-me-in-production
    database: infisical
  primary:
    persistence:
      size: 8Gi
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2
      memory: 2Gi

# Redis (optional - if using in-cluster)
redis:
  enabled: true
  auth:
    enabled: false
  master:
    persistence:
      size: 2Gi
  resources:
    requests:
      cpu: 250m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 1Gi
```

## Using External Databases

To use managed PostgreSQL and Redis (RDS, Cloud SQL, ElastiCache, etc.), disable the in-cluster services:

```yaml
postgresql:
  enabled: false

redis:
  enabled: false
```

Then configure the connection strings in the secret:

```bash
kubectl create secret generic infisical-secrets \
  --from-literal=DB_CONNECTION_URI="postgresql://user:password@rds-instance.amazonaws.com:5432/infisical" \
  --from-literal=REDIS_URL="rediss://redis-cluster.cache.amazonaws.com:6380" \
  # ... other variables
  -n infisical
```

## Scaling

### Horizontal Scaling

Increase the number of replicas in `values.yaml`:

```yaml
replicaCount: 5  # Scale to 5 replicas
```

Apply the change:

```bash
helm upgrade infisical infisical/infisical-standalone-postgres \
  --namespace infisical \
  --values values.yaml
```

Or use kubectl directly:

```bash
kubectl scale deployment infisical --replicas=5 -n infisical
```

### Autoscaling

Enable Horizontal Pod Autoscaler (HPA):

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Pod Security

### Non-Root User

The default configuration runs Infisical as a non-root user (UID 1001):

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1001
  fsGroup: 1001

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
```

### Pod Security Policy

For Kubernetes clusters with Pod Security Policies (PSP) enabled, ensure the Infisical deployment complies:

```bash
kubectl label pod -l app=infisical restricted=true -n infisical
```

## Networking

### Network Policy

Create a NetworkPolicy to isolate Infisical traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: infisical-network-policy
  namespace: infisical
spec:
  podSelector:
    matchLabels:
      app: infisical
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 5432  # PostgreSQL
        - protocol: TCP
          port: 6379  # Redis
    - to:
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 53  # DNS
```

### Ingress with TLS

Use cert-manager and Let's Encrypt for automated TLS:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: infisical-cert
  namespace: infisical
spec:
  secretName: infisical-tls
  issuerRef:
    name: letsencrypt-prod
  commonName: secrets.example.com
  dnsNames:
    - secrets.example.com
```

Then configure Ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: infisical-ingress
  namespace: infisical
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - secrets.example.com
      secretName: infisical-tls
  rules:
    - host: secrets.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: infisical
                port:
                  number: 8080
```

## Persistence

Create PersistentVolumeClaims for PostgreSQL and Redis data:

```yaml
postgresql:
  primary:
    persistence:
      enabled: true
      storageClassName: fast-ssd
      size: 20Gi

redis:
  master:
    persistence:
      enabled: true
      storageClassName: fast-ssd
      size: 5Gi
```

## Monitoring and Logging

### Metrics

Infisical exposes metrics via the `/metrics` endpoint (OpenTelemetry format):

```bash
kubectl port-forward svc/infisical 8080:8080 -n infisical
curl http://localhost:8080/metrics
```

### Logs

View logs from all Infisical replicas:

```bash
kubectl logs -l app=infisical -n infisical --all-containers=true -f
```

### Prometheus Integration

Create a ServiceMonitor for Prometheus:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: infisical
  namespace: infisical
spec:
  selector:
    matchLabels:
      app: infisical
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

## Backup and Recovery

### Backup PostgreSQL

If using in-cluster PostgreSQL:

```bash
kubectl exec -it infisical-postgresql-0 -n infisical -- \
  pg_dump -U infisical infisical | gzip > backup.sql.gz
```

For managed PostgreSQL (RDS, Cloud SQL), use the managed service's backup tools.

### Backup Redis

For in-cluster Redis:

```bash
kubectl exec -it infisical-redis-master-0 -n infisical -- \
  redis-cli BGSAVE
kubectl cp infisical/infisical-redis-master-0:/data/dump.rdb ./redis_backup.rdb
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n infisical
kubectl describe pod <pod-name> -n infisical
```

### View Logs

```bash
kubectl logs <pod-name> -n infisical
```

### Port Forward for Testing

```bash
kubectl port-forward svc/infisical 8080:8080 -n infisical
curl http://localhost:8080/api/status
```

### Check Events

```bash
kubectl get events -n infisical --sort-by='.lastTimestamp'
```

## Upgrading

To upgrade Infisical on Kubernetes:

1. Backup PostgreSQL (see Backup and Recovery section)

2. Update the chart:
```bash
helm repo update
```

3. Upgrade the release:
```bash
helm upgrade infisical infisical/infisical-standalone-postgres \
  --namespace infisical \
  --values values.yaml
```

4. Monitor the rollout:
```bash
kubectl rollout status deployment/infisical -n infisical
```

Schema migrations run automatically during pod startup.
