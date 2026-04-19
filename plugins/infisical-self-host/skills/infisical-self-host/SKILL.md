---
name: infisical-self-host
description: Deploy and operate Infisical self-hosted instances with Docker, Docker Compose, and Kubernetes. Covers architecture, environment variables, ENCRYPTION_KEY management, database setup, Redis configuration, production hardening, FIPS compliance, scaling, and high availability patterns.
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

## Guiding Principles

1. **ENCRYPTION_KEY is Critical**: This key encrypts all secrets at rest. It is 16 bytes (32 hex characters), generated with `openssl rand -hex 16`, and **cannot be recovered if lost**. Back it up and rotate it carefully following Infisical's rotation procedures.

2. **AUTH_SECRET is Required**: This key is used for session and JWT signing. It is 32 bytes (base64), generated with `openssl rand -base64 32`, and must be stable across restarts.

3. **Database Requirements**: PostgreSQL 14+ is required. Always backup your database before upgrading Infisical. Schema migrations run automatically on boot (since v0.111.0-postgres).

4. **Redis Configuration**: Redis 6.2+ is required. Cluster mode is NOT supported; use standalone or Redis Sentinel for high availability. Standalone mode is simplest for development; use Sentinel for production HA.

5. **Stateless Architecture**: Infisical is stateless. Scale horizontally by adding more replicas. All state lives in PostgreSQL and Redis.

6. **FIPS Compliance**: FIPS 140-2 mode is available via the `infisical/infisical:latest-fips` image. Enable with `FIPS_ENABLED=true` and appropriate Node.js options.

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
