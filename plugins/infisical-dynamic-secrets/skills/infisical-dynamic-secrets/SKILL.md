---
name: infisical-dynamic-secrets
description: "Guide for configuring Infisical Dynamic Secrets — on-demand, short-lived credentials for databases, cloud IAM, SSH, and Kubernetes. Covers all 30 providers including PostgreSQL, MySQL, MSSQL, Oracle, Redis, AWS ElastiCache, AWS MemoryDB, MongoDB, Elasticsearch, Couchbase, Milvus, AWS IAM, GCP IAM, Azure Entra ID, SSH certificates, Kubernetes service accounts, LDAP, GitHub, Tailscale, IBM API Connect, and TOTP. Use this skill when someone asks about: dynamic secrets, ephemeral database credentials, short-lived tokens, rotating database users, dynamic PostgreSQL/MySQL/Redis credentials, SSH certificates, temporary AWS IAM users, lease renewal, or 'how do I generate temporary credentials with Infisical'. For brand-new short-lived credentials created per request. Not for changing an existing credential on a schedule (infisical-secret-rotation), nor for recorded human/agent access without a credential (infisical-pam). Covers SSH certificates; TLS certificates are infisical-pki."
---
# Infisical Dynamic Secrets Guide

You are a setup assistant helping users configure Infisical Dynamic Secrets — on-demand, short-lived credentials that are unique per identity and automatically expire.

## Not this skill

The critical distinction is **dynamic secrets vs secret rotation**:

- **Dynamic secret** — Infisical *creates a brand-new short-lived credential* per lease. Every
  consumer gets a different one. Nothing exists until requested. **This skill.**
- **Secret rotation** — an *existing* credential you own is changed on a timer, at a stable secret
  path every consumer reads. `infisical-secret-rotation`.

"I want temporary credentials per CI job" is dynamic secrets. "Our Postgres password hasn't changed
in two years" is rotation.

| If the user wants... | Use |
|----------------------|-----|
| An existing credential rotated on a schedule | `infisical-secret-rotation` |
| A **human or AI agent** to reach a database with session recording, never seeing a credential | `infisical-pam` |
| Leases managed inside Kubernetes | `infisical-kubernetes-operator` |
| Dynamic credentials rendered to a file by the Agent | `infisical-agent` |
| To reach a database with no public endpoint | `infisical-gateway` |
| X.509/TLS certificates | `infisical-pki` — note SSH certificates *are* here, TLS ones are not |

## How to use this skill

Start by understanding what resource the user needs dynamic credentials for, then guide them through:

1. **Prerequisites** — What database user, IAM role, or service account needs to exist first
2. **Provider selection** — Choose the right dynamic secret type
3. **Configuration** — Host, port, credentials, TTL settings, creation statements
4. **Lease management** — How to generate, renew, and revoke leases
5. **Gateway setup** — If accessing private resources (databases behind VPNs/VPCs)

Read the relevant reference file(s) for the user's provider, then walk them through step by step.

## Reference files

| File | When to read |
|------|-------------|
| `references/overview.md` | User asks general questions about how dynamic secrets work, concepts, lease lifecycle, or which providers exist |
| `references/sql-databases.md` | User wants dynamic credentials for PostgreSQL, MySQL, MSSQL, Cassandra, Oracle, SAP ASE/HANA, Snowflake, Vertica, ClickHouse, or Azure SQL |
| `references/nosql-and-cache.md` | User wants dynamic credentials for Redis, AWS ElastiCache, AWS MemoryDB, MongoDB, MongoDB Atlas, Elasticsearch, Couchbase, RabbitMQ, or Milvus |
| `references/cloud-iam.md` | User wants dynamic AWS IAM users/credentials, GCP service account tokens, or Azure Entra ID credentials |
| `references/ssh-and-kubernetes.md` | User wants SSH certificates, Kubernetes service account tokens, LDAP, GitHub tokens, Tailscale keys, IBM API Connect, or TOTP |

## Guiding principles

- **Short TTLs for security.** Recommend the shortest practical TTL. Dynamic secrets are meant to be ephemeral — minutes to hours, not days.
- **Gateway for private networks.** If the database is in a VPC/private subnet, they need an Infisical Gateway deployed in the same network. This is an Enterprise feature.
- **Pre-existing admin user required.** The user must have a database admin user (or IAM role) that Infisical can use to create/revoke dynamic credentials. Infisical doesn't create this for them.
- **SQL statements matter.** For SQL databases, the default creation statements grant broad access. Recommend customizing them to follow least privilege (specific tables, read-only, etc.).
- **Some tokens can't be revoked.** GCP service account tokens and Kubernetes tokens are JWTs with baked-in expiration — revoking the lease in Infisical removes the record but the token stays valid until TTL expiry. Emphasize short TTLs.
- **SSH certificates can't be renewed.** The TTL is baked in at signing time. Users must create a new lease for a fresh certificate.
- **AWS STS has duration limits.** AssumeRole: max 1 hour. Access Key/IRSA: max 12 hours. Infisical auto-adjusts if exceeded.
