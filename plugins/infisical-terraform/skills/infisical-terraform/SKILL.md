---
name: infisical-terraform
description: |
  Expert guidance for the Infisical Terraform Provider. Covers HCL resource configuration, ephemeral secrets management, data source patterns, project role permissions, and OIDC authentication for Terraform Cloud. Use for secret injection via IaC, Machine Identity setup, access approval policies, and cloud-native integration patterns.
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

1. **Ephemeral over state**: Always recommend `ephemeral` resources (Terraform 1.10+) for secrets—values never land in state files.
2. **Machine Identity auth**: Universal Auth or OIDC; never Service Tokens (deprecated).
3. **Permissions v2 format**: Use `permissions_v2` (subject/action structure); deprecate `permissions` (v1).
4. **OIDC for Terraform Cloud**: This is the recommended production pattern.
5. **Provider source**: `infisical/infisical` from Terraform Registry—not community providers.
6. **Folder path defaults**: `folder_path = "/"` if omitted.

## When to send users to references

- Auth confusion or env var setup → provider-setup.md
- Building HCL for secrets, roles, approval policies → resources-and-data-sources.md
- TFC + Infisical step-by-step → terraform-cloud-oidc.md
