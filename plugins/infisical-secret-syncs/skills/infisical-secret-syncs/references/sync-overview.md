# Secret Syncs Overview

## What are Secret Syncs?

Secret Syncs are project-level resources that automatically push secrets from an Infisical source (environment + folder path) to third-party services. When secrets change in Infisical, the sync propagates those changes to the destination.

**Infisical is the source of truth.** Secrets at the destination not present in Infisical may be overwritten depending on the initial sync behavior setting.

## Prerequisites

Every sync requires an **App Connection** — an authenticated connection to the target service with the correct permissions. Create the App Connection first, then create the sync.

## Common Setup Workflow

1. **Create App Connection** for the target service (one-time setup, reusable across syncs)
2. **Navigate to** Project → Integrations → Secret Syncs tab → Add Sync
3. **Select destination** (e.g., AWS Secrets Manager, GitHub, etc.)
4. **Configure Source:**
   - Environment: project environment slug (e.g., `dev`, `staging`, `prod`)
   - Secret Path: folder path (e.g., `/`, `/api-keys`, `/database`)
5. **Configure Destination:** provider-specific fields (region, vault URL, repo, etc.)
6. **Configure Sync Options:**
   - Initial Sync Behavior
   - Key Schema (recommended)
   - Auto-Sync toggle
   - Disable Secret Deletion toggle
7. **Name the sync** and create

## Key Concepts

### Initial Sync Behavior

Controls what happens on the first sync:

When configuring via the API, use these exact enum values — the UI labels differ from the wire
values:

| UI label | API value | Behavior |
|----------|-----------|----------|
| **Overwrite Destination** | `overwrite-destination` | Removes any secrets at the destination not present in Infisical |
| **Import — Prioritize Infisical** | `import-prioritize-source` | Imports existing destination secrets into Infisical first; Infisical (source) values win on conflict |
| **Import — Prioritize Destination** | `import-prioritize-destination` | Imports existing destination secrets into Infisical first; destination values win on conflict |

The import values are named after **source/destination**, not after the provider. There is no
`import-prioritize-infisical`, `import-prioritize-vercel`, or `import-prioritize-hashicorp-vault`.

> Not all destinations support importing. GitHub and Cloudflare Workers, among others, only
> support `overwrite-destination`.

### Key Schema

A template that transforms secret names when syncing. Uses handlebars-style placeholders:

- `{{secretKey}}` — the secret's key. **Required, and must appear exactly once.**
- `{{environment}}` — the environment slug (e.g. `dev`, `staging`, `prod`). Optional.

Outside the placeholders, only alphanumerics (`a-z`, `A-Z`, `0-9`), dashes, underscores, and
slashes are allowed.

**Example:** Key schema `INFISICAL_{{secretKey}}` transforms Infisical key `DATABASE_URL` into `INFISICAL_DATABASE_URL` at the destination.

**Why use it:** Destination secrets that don't match the schema are never updated or deleted by
Infisical, so the schema is what scopes Infisical's blast radius at the destination. Highly
recommended for all syncs.

When importing secrets, the key schema is stripped from keys before importing into Infisical.

### Mapping Behavior (AWS Secrets Manager only)

- **One-to-One:** Each Infisical secret becomes a separate secret in the destination
- **Many-to-One:** All Infisical secrets are packed into a single destination secret (as JSON key-value pairs)

### Auto-Sync

Enabled by default. Secrets automatically sync when changes occur in the Infisical source. Disable for manual-only syncing.

### Disable Secret Deletion

When enabled, Infisical will not remove secrets from the destination. Use this if you manage some secrets manually outside of Infisical.

## Supported Destinations (48)

The complete list, with the API `destination` value for each:

**Cloud secret managers**

| Destination | API value |
|-------------|-----------|
| AWS Secrets Manager | `aws-secrets-manager` |
| AWS Parameter Store | `aws-parameter-store` |
| GCP Secret Manager | `gcp-secret-manager` |
| Azure Key Vault | `azure-key-vault` |
| Azure App Configuration | `azure-app-configuration` |
| OCI Vault | `oci-vault` |
| Hashicorp Vault | `hashicorp-vault` |
| 1Password | `1password` |
| Infisical (another instance) | `external-infisical` |

**CI/CD**

| Destination | API value |
|-------------|-----------|
| GitHub | `github` |
| GitLab | `gitlab` |
| Bitbucket | `bitbucket` |
| CircleCI | `circleci` |
| Travis CI | `travis-ci` |
| TeamCity | `teamcity` |
| Azure DevOps | `azure-devops` |
| Octopus Deploy | `octopus-deploy` |
| Spacelift | `spacelift` |
| Terraform Cloud | `terraform-cloud` |
| Rundeck | `rundeck` |

**Hosting and PaaS**

| Destination | API value |
|-------------|-----------|
| Vercel | `vercel` |
| Netlify | `netlify` |
| Cloudflare Workers | `cloudflare-workers` |
| Cloudflare Pages | `cloudflare-pages` |
| Railway | `railway` |
| Render | `render` |
| Fly.io | `flyio` |
| Heroku | `heroku` |
| Northflank | `northflank` |
| Digital Ocean App Platform | `digital-ocean-app-platform` |
| Qovery | `qovery` |
| Cloud 66 | `cloud-66` |
| Laravel Forge | `laravel-forge` |
| OVH | `ovh` |

**Data and analytics**

| Destination | API value |
|-------------|-----------|
| Databricks | `databricks` |
| Snowflake | `snowflake` |
| Supabase | `supabase` |
| Hasura Cloud | `hasura-cloud` |

**Platform, workflow, and monitoring**

| Destination | API value |
|-------------|-----------|
| Humanitec | `humanitec` |
| Camunda | `camunda` |
| Windmill | `windmill` |
| Chef | `chef` |
| Checkly | `checkly` |
| Zabbix | `zabbix` |
| Trigger.dev | `trigger-dev` |
| Devin | `devin` |
| Ona | `ona` |
| Azure Entra ID SCIM | `azure-entra-id-scim` |

There is **no Jenkins sync**. Octopus Deploy is its own destination, not a Jenkins bridge. If a
user needs Jenkins, point them at the CLI or the API rather than a sync.

## Secret Imports for Multiple Paths

If you need to sync secrets from multiple folder locations into a single sync, use Infisical's **Secret Imports** feature to consolidate them into one path first, then sync that path.
