# Infisical AI Skills

## Available Skills

### infisical-setup

**Description:** Interactive setup guide for integrating Infisical into your projects — CLI, Docker, Kubernetes, CI/CD, SDKs, and machine identity auth.

**Location:** `skills/infisical-setup/SKILL.md`

**Use when:** You need to integrate Infisical secret management into an application, container, pipeline, or infrastructure. Covers CLI setup, all 6 SDKs (Node.js, Python, Go, Java, .NET, Ruby), Docker build/runtime injection, Kubernetes Operator, GitHub Actions/GitLab CI, and all 12 machine identity auth methods.

### infisical-secret-syncs

**Description:** Guide for configuring Infisical Secret Syncs to push secrets to 38+ third-party services including AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, GitHub, Vercel, HashiCorp Vault, and more.

**Location:** `skills/infisical-secret-syncs/SKILL.md`

**Use when:** You need to push secrets from Infisical to another service. Covers App Connections, key schemas, mapping behavior (one-to-one vs many-to-one), initial sync options, and provider-specific configuration for all supported destinations.

### infisical-dynamic-secrets

**Description:** Guide for configuring Infisical Dynamic Secrets — on-demand, short-lived credentials for databases, cloud IAM, SSH, and Kubernetes across 27 providers.

**Location:** `skills/infisical-dynamic-secrets/SKILL.md`

**Use when:** You need temporary, auto-expiring credentials for databases (PostgreSQL, MySQL, Redis, MongoDB), cloud providers (AWS IAM, GCP), SSH access, or Kubernetes service accounts. Covers lease lifecycle, TTL management, creation statements, and Gateway setup for private networks.

### infisical-agent

**Description:** Guide for configuring the Infisical Agent — a client daemon that manages auth token lifecycle and renders secrets to files via Go templates.

**Location:** `skills/infisical-agent/SKILL.md`

**Use when:** You need the Infisical Agent to inject secrets into containers or VMs without modifying application code. Covers YAML config format, all 6 auth methods, template functions (`listSecrets`, `getSecretByName`, `dynamicSecret`), sinks, polling, and deployment patterns for Docker, ECS, and Kubernetes.
