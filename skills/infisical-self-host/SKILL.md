---
name: infisical-self-host
description: Deploy and operate Infisical self-hosted instances with Docker, Docker Compose, and Kubernetes. Covers architecture, environment variables, ENCRYPTION_KEY management, PostgreSQL setup, Redis configuration (including the required noeviction policy), production hardening, FIPS 140-3 compliance, scaling, and high availability patterns. For deploying the Infisical platform itself. Not for the Kubernetes Operator, which is a separate Helm chart (infisical-kubernetes-operator), nor for using Infisical once running (infisical-setup).
triggers:
  - self-host infisical
  - deploy infisical
  - docker compose infisical
  - infisical docker
  - helm chart infisical
  - kubernetes infisical
  - ENCRYPTION_KEY
  - infisical environment variables
  - production deployment infisical
  - FIPS infisical
  - scale infisical
  - ha infisical
---

# Infisical Self-Hosted Deployment

This skill guides you through deploying, configuring, and operating Infisical in self-hosted environments. Whether you are running Infisical on Docker, Docker Compose, or Kubernetes, this resource covers essential setup, security hardening, scaling, and maintenance patterns.

## Not this skill

| If the user wants... | Use |
|----------------------|-----|
| To deploy the **Kubernetes Operator** (also a Helm chart, different thing) | `infisical-kubernetes-operator` |
| To reach a private resource from Infisical | `infisical-gateway` |
| To configure SSO or SCIM on their instance | `infisical-sso` |
| Roles, permissions, audit log streams | `infisical-access-control` |
| To use Infisical once it is running | `infisical-setup` |
| An external KMS or HSM backing the root key | `infisical-kms` |

The Helm confusion is worth pre-empting: the `secrets-operator` chart installs the **operator**;
this skill covers the chart that installs the **platform**. Both come from the same Cloudsmith repo.

## Guiding Principles

1. **ENCRYPTION_KEY is Critical**: This key encrypts all secrets at rest and **cannot be recovered if lost**. Back it up and rotate it carefully following Infisical's rotation procedures.
   - Standard deployments: a random 16-byte hex string — `openssl rand -hex 16`
   - **FIPS-enabled deployments: a 256-bit base64 key instead** — `openssl rand -base64 32`

2. **AUTH_SECRET is Required**: This key is used for session and JWT signing. It is 32 bytes (base64), generated with `openssl rand -base64 32`, and must be stable across restarts.

3. **Database Requirements**: PostgreSQL is the only supported database. Use 14+ for compatibility; Infisical is extensively tested on 16. Always backup your database before upgrading Infisical. Schema migrations run automatically on boot (since v0.111.0-postgres).

4. **Redis is a hard dependency, not just a cache**: Beyond caching it holds the background job queue, distributed locks, cross-instance coordination state, and rate-limit counters. **The instance will not start unless one of `REDIS_URL`, `REDIS_SENTINEL_HOSTS`, or `REDIS_CLUSTER_HOSTS` is set**, and a running instance is degraded while Redis is unreachable.
   - Use Redis 6.x or 7.x; at least 6.2 is advised
   - All three topologies are supported: standalone, Sentinel, and Cluster
   - **Active-passive is recommended.** Active-active has not been tested and may behave in undocumented ways
   - **Set the eviction policy to `noeviction`.** This is required, not a tuning suggestion — evicting keys under memory pressure would silently drop queued work
   - Enable persistence (AOF, or at minimum RDB snapshots) and back Redis up. Pending secret rotations, syncs, and webhook deliveries live there; a Redis that comes back empty loses them
   - Give Redis the same availability target as the app instances — an unreplicated Redis is a single point of failure for the whole deployment

5. **Stateless Architecture**: Infisical is stateless. Scale horizontally by adding more replicas. All state lives in PostgreSQL and Redis. Each instance needs no more than 2–4 CPU cores and 4–8 GB memory; add containers rather than growing one.

6. **FIPS Compliance**: Infisical is compliant with **FIPS 140-3**. Deploy the separate **`infisical/infisical-fips`** Docker image (an Enterprise-only image, not a tag on the standard repo) and set `FIPS_ENABLED=true`. Remember the `ENCRYPTION_KEY` format changes to 256-bit base64 in FIPS mode.

## Quick Start

- **Docker Standalone**: Pull `infisical/infisical:<version>`, set environment variables, run on port 8080.
- **Docker Compose**: Use `docker-compose.prod.yml` from the repository with PostgreSQL and Redis services.
- **Kubernetes**: Deploy via Helm chart `infisical-standalone-postgres` from Cloudsmith registry with optional managed databases.

## Reference Guides

### [Environment Variables](./references/environment-variables.md)
Complete reference for all configuration environment variables, including:
- Required keys (ENCRYPTION_KEY, AUTH_SECRET, database, Redis)
- Database and replication setup
- Redis with Sentinel support
- SMTP configuration
- OAuth/SSO providers
- FIPS and telemetry settings
- Security options

### [Docker Deployment](./references/docker-deployment.md)
Docker and Docker Compose deployment patterns, including:
- Standalone container setup
- Docker Compose production stack
- Image variants (standard and FIPS)
- Production hardening with security capabilities and read-only filesystems
- Health checks

### [Kubernetes Deployment](./references/kubernetes-deployment.md)
Kubernetes and Helm deployment guide, including:
- Helm chart installation and configuration
- Secret creation and management
- Optional PostgreSQL and Redis (Bitnami charts)
- Pod security and RBAC
- Networking policies and Ingress/TLS

### [Scaling and High Availability](./references/scaling-and-ha.md)
Production scaling patterns and HA architecture, including:
- Horizontal scaling (adding replicas)
- Sizing guidelines for Infisical, PostgreSQL, and Redis
- Database read replicas
- Redis Sentinel for HA
- Backup and upgrade procedures
- License server firewall rules
