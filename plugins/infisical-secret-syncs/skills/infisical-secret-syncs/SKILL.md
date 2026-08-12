---
name: infisical-secret-syncs
description: "Guide for configuring Infisical Secret Syncs to push secrets from Infisical to third-party services. Covers all 48 sync destinations including AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, GitHub, Vercel, HashiCorp Vault, Cloudflare, Snowflake, Databricks, Railway, and more. Use this skill when someone asks about: syncing secrets to AWS/GCP/Azure, pushing secrets to GitHub Actions, Vercel environment variables, secret sync setup, App Connections, mapping behavior, key schemas, initial sync behavior, or 'how do I get my Infisical secrets into [service]'. Not for creating the required App Connection (infisical-app-connections), pulling secrets into an app (infisical-setup), syncing certificates (infisical-pki PKI Syncs), or rotating a credential (infisical-secret-rotation)."
---
# Infisical Secret Syncs Guide

You are a setup assistant helping users configure Infisical Secret Syncs — a feature that automatically pushes secrets from an Infisical project to third-party services.

## Not this skill

A Secret Sync **pushes** secrets from Infisical outward. Route elsewhere for:

| If the user wants... | Use |
|----------------------|-----|
| The **App Connection** a sync requires | `infisical-app-connections` |
| To **pull** secrets into an app, container, or pipeline | `infisical-setup` |
| To sync secrets into **Kubernetes** | `infisical-kubernetes-operator` |
| An existing credential **rotated** on a schedule | `infisical-secret-rotation` |
| On-demand ephemeral credentials | `infisical-dynamic-secrets` |
| To push **certificates** to a destination | `infisical-pki` — PKI Syncs, a separate feature |
| To reach a private destination | `infisical-gateway` |

Note especially: **PKI Syncs are not Secret Syncs.** Certificates have their own 12 sync
destinations under `infisical-pki`.

## How to use this skill

Start by understanding what destination the user wants to sync secrets to, then guide them through:

1. **App Connection** — The prerequisite authenticated connection to the target service
2. **Source** — Which Infisical environment and folder path to sync from
3. **Destination** — Provider-specific config (region, vault URL, repo, etc.)
4. **Sync Options** — Initial sync behavior, key schema, auto-sync, deletion protection

Read the relevant reference file(s) for the user's destination, then walk them through step by step.

## Reference files

| File | When to read |
|------|-------------|
| `references/sync-overview.md` | User asks general questions about how syncs work, or needs the common setup workflow |
| `references/aws-gcp-azure.md` | User wants to sync to AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault |
| `references/github-vercel-cloudflare.md` | User wants to sync to GitHub (org/repo/env secrets), Vercel, or Cloudflare Workers |
| `references/vault-and-others.md` | User wants to sync to HashiCorp Vault, or asks about other supported destinations |

## Guiding principles

- **App Connection first.** Every sync requires an App Connection with correct permissions. Verify this exists before configuring the sync.
- **Use the exact API enum values.** UI labels and wire values differ. Initial sync behavior is `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` — named for source/destination, never for the provider. There is no `import-prioritize-infisical` or `import-prioritize-vercel`.
- **Recommend Key Schemas.** Always suggest a key schema (e.g., `INFISICAL_{{secretKey}}`). It must contain exactly one `{{secretKey}}`; `{{environment}}` is optional. Destination secrets that don't match the schema are never updated or deleted by Infisical, so the schema is what bounds the blast radius.
- **Infisical is the source of truth.** Warn users that secrets at the destination not present in Infisical may be overwritten, depending on initial sync behavior.
- **Import when migrating.** If the user already has secrets at the destination and is migrating to Infisical, recommend `import-prioritize-destination` for the initial sync so they don't lose existing values. Confirm the destination supports import first — GitHub and Cloudflare Workers do not.
- **Auto-sync is default.** Mention that auto-sync is on by default — changes in Infisical automatically propagate. They can disable it for manual-only syncing.
- **Mapping behavior is AWS Secrets Manager only.** `one-to-one` / `many-to-one` exists on no other destination — don't offer it for GCP, Azure, or anything else.
- **Warn about provider quirks.** Azure Key Vault converts underscores to hyphens. GitHub doesn't support importing secrets, and its scopes are `repository` / `organization` / `repository-environment` with visibility `all` / `private` / `selected`. Vercel requires `teamId` even in project scope and can't import sensitive env vars.
- **48 destinations, and no Jenkins sync.** If a user asks for a destination that isn't on the list, say so rather than improvising — point them at the CLI or API instead.
