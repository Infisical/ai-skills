---
name: infisical-terraform
description: |
  Expert guidance for the Infisical Terraform Provider. Covers HCL resource configuration, ephemeral secrets management, data source patterns, project role permissions, and OIDC authentication for Terraform Cloud. Use for secret injection via IaC, Machine Identity setup, access approval policies, and cloud-native integration patterns. Not for getting secrets into a running app (infisical-setup) or raw REST calls (infisical-api).
triggers:
  - terraform
  - HCL
  - infisical provider
  - ephemeral resource
  - terraform state secrets
  - terraform cloud OIDC
  - infisical secrets management
  - infisical resource
---

# Infisical Terraform Provider

Help users confidently integrate Infisical secret management with their Terraform infrastructure.

## Not this skill

| If the user wants... | Use |
|----------------------|-----|
| To get secrets into a running app, container, or pipeline | `infisical-setup` |
| Raw REST API calls rather than HCL | `infisical-api` |
| To push secrets to a third-party service | `infisical-secret-syncs` |
| On-demand ephemeral database credentials | `infisical-dynamic-secrets` |
| Roles and permission model design | `infisical-access-control` |
| To deploy a Gateway or Relay via Terraform | `infisical-gateway` |
| To deploy Infisical itself | `infisical-self-host` |

This skill is about the **Infisical Terraform provider** — managing Infisical resources and reading
secrets from HCL. It is not about using Terraform generally.

## What users typically ask for

- "How do I use Infisical with Terraform?" — Provider setup and auth
- "How do I prevent secrets in my Terraform state?" — Ephemeral resources
- "How do I set up Terraform Cloud with Infisical?" — OIDC integration
- "How do I configure project roles and permissions?" — Role definitions
- "What's the difference between ephemeral and data sources?" — Resource patterns

## Quick routing

- **Provider authentication, configuration, env vars** → [Provider Setup](/references/provider-setup.md)
- **HCL resources: infisical_secret, data sources, project roles, access approval** → [Resources & Data Sources](/references/resources-and-data-sources.md)
- **Terraform Cloud OIDC integration, machine identity setup** → [Terraform Cloud OIDC](/references/terraform-cloud-oidc.md)

## Key principles to uphold

1. **Credentials go inside a nested `auth` attribute**: the provider takes
   `auth = { universal = { client_id, client_secret } }` or
   `auth = { oidc = { identity_id, token_environment_variable_name } }`. Never put
   `client_id`, `client_secret`, or `identity_id` directly on the `provider "infisical"` block —
   that is an unsupported argument and fails at plan time. (Legacy `service_token` is the one
   exception and does sit at the top level.)
2. **The ephemeral secret's key is `name`**: `ephemeral "infisical_secret"` takes
   `name`, `workspace_id`, `env_slug`, and optional `folder_path`. There is no `secret_key`
   argument.
3. **Ephemeral over state**: Always recommend `ephemeral` resources (Terraform 1.10+) for secrets—values never land in state files. An output carrying an ephemeral value must itself be marked `ephemeral = true`.
4. **Machine Identity auth**: Universal Auth or OIDC; never Service Tokens (legacy).
5. **Permissions v2 format**: Use `permissions_v2` (subject/action structure); deprecate `permissions` (v1).
6. **OIDC for Terraform Cloud**: This is the recommended production pattern.
7. **Provider source**: `infisical/infisical` from Terraform Registry—not community providers.
8. **Folder path defaults**: `folder_path = "/"` if omitted.
9. **Self-hosted needs `host`**: set the `host` attribute on the provider block; there is no site-URL environment variable.

## When to send users to references

- Auth confusion or env var setup → provider-setup.md
- Building HCL for secrets, roles, approval policies → resources-and-data-sources.md
- TFC + Infisical step-by-step → terraform-cloud-oidc.md
