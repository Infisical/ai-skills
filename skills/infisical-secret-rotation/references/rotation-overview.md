# Secret Rotation Overview

## What rotation is

A Secret Rotation is a project-level resource that, on a fixed interval, changes the credential
of an **account that already exists** in a third-party system and writes the new values into
Infisical secrets at a path you choose. Consumers keep reading the same secret names; the values
underneath change.

Rotation is an **Enterprise / paid** feature.

## Rotation vs dynamic secrets

| | Secret Rotation | Dynamic Secrets |
|---|---|---|
| Account lifecycle | Pre-existing, you own it | Created on demand by Infisical |
| Consumers | All read the same secret path | Each lease gets its own credential |
| Trigger | Timer (`rotationInterval` days) | A request for a lease |
| Cleanup | Old credential revoked after the next rotation | Credential revoked at lease expiry |
| Typical use | A production DB password that must not go stale | Per-CI-job or per-engineer database access |

Do not offer rotation when the user wants isolation per consumer, and do not offer dynamic
secrets when the user needs one stable credential that many services already point at.

## The two rotation models

### Dual-phase (23 of 28 providers)

Two credential sets exist in an overlapping cycle, so there is always a valid credential.

Each set moves through three states:

- **Active** — the primary credential, returned by the mapped secrets
- **Inactive** — replaced but still valid; revoked at the *next* rotation
- **Revoked** — permanently invalidated and deleted

With a 30-day interval:

| Day | Set 1 | Set 2 | Set 3 |
|-----|-------|-------|-------|
| 0 | Active | — | — |
| 30 | Inactive (still valid) | Active | — |
| 60 | **Revoked** | Inactive (still valid) | Active |
| 90 | — | **Revoked** | Inactive |

The guarantee this buys you: a credential fetched at any point during a set's active window stays
valid for at least one further full interval. That is the grace period applications use to pick up
the new value.

The corollary, which matters: a credential is revoked after **two** intervals. An application that
caches a secret for longer than 2× `rotationInterval` will eventually present a revoked
credential. Cache TTLs must stay well under that.

### Single-phase (5 providers)

One credential set, updated in place. **Old credentials become invalid immediately** — there is no
overlap. Clients holding the previous value fail to authenticate until they re-read the secret.

The five single-phase providers:

| Provider | Type value |
|----------|-----------|
| Auth0 Client Secret | `auth0-client-secret` |
| LDAP Password | `ldap-password` |
| Unix/Linux Local Account | `unix-linux-local-account` |
| Windows Local Account | `windows-local-account` |
| HP iLO Local Account | `hp-ilo-local-account` |

These are single-phase because the target system only supports one active credential at a time, or
because the account is inherently singular (a login account).

**Recommended handling:** disable auto-rotation (`isAutoRotationEnabled: false`) and trigger
rotations manually during a maintenance window. Coordinate dependent services so they re-read
promptly, and watch for auth failures afterward.

## Scheduling

| Field | Type | Meaning |
|-------|------|---------|
| `rotationInterval` | integer, **minimum 1** | Interval **in days** between automatic rotations |
| `rotateAtUtc` | `{ hours: 0-23, minutes: 0-59 }` | Time of day rotation runs, in UTC. Defaults to midnight `00:00` UTC |
| `isAutoRotationEnabled` | boolean, default `true` | Whether the timer runs at all |

`rotationInterval` is a day count. It is not hours and not a cron expression. Setting it to `1`
means daily.

## Common configuration shape

Every rotation is created with the same base fields plus provider-specific
`parameters` and `secretsMapping`:

```json
{
  "name": "prod-postgres-rotation",
  "projectId": "<project-id>",
  "description": "Rotates the prod app DB user",
  "connectionId": "<app-connection-uuid>",
  "environment": "prod",
  "secretPath": "/database",
  "isAutoRotationEnabled": true,
  "rotationInterval": 30,
  "rotateAtUtc": { "hours": 3, "minutes": 0 },
  "parameters": { },
  "secretsMapping": { }
}
```

Notes on the base fields:

- `name` is a slug
- `description` is capped at 256 characters
- `connectionId` is the UUID of an existing App Connection whose type matches the rotation
- `secretPath` is where the mapped secrets are written; trailing slashes are stripped
- `parameters` — what to rotate and how (provider-specific)
- `secretsMapping` — which Infisical secret **names** receive each rotated field

### secretsMapping

`secretsMapping` maps a provider's credential fields onto secret names in your project. For a SQL
rotation:

```json
"secretsMapping": {
  "username": "DB_USERNAME",
  "password": "DB_PASSWORD"
}
```

After rotation, `/database/DB_USERNAME` and `/database/DB_PASSWORD` hold the active credential.
Point your application at those names and it never needs to know rotation is happening.

Secret names must be valid Infisical secret names.

## All 28 rotation providers

Each requires an App Connection of the listed type.

### Databases

| Rotation | Type value | App Connection |
|----------|-----------|----------------|
| PostgreSQL Credentials | `postgres-credentials` | `postgres` |
| MySQL Credentials | `mysql-credentials` | `mysql` |
| Microsoft SQL Server Credentials | `mssql-credentials` | `mssql` |
| OracleDB Credentials | `oracledb-credentials` | `oracledb` |
| MongoDB Credentials | `mongodb-credentials` | `mongodb` |
| Redis Credentials | `redis-credentials` | `redis` |
| Snowflake User Key Pair | `snowflake-user-key-pair` | `snowflake` |

### Cloud and identity

| Rotation | Type value | App Connection |
|----------|-----------|----------------|
| AWS IAM User Secret | `aws-iam-user-secret` | `aws` |
| Azure Client Secret | `azure-client-secret` | `azure-client-secrets` |
| Okta Client Secret | `okta-client-secret` | `okta` |
| Auth0 Client Secret | `auth0-client-secret` | `auth0` |
| LDAP Password | `ldap-password` | `ldap` |
| Databricks Service Principal Secret | `databricks-service-principal-secret` | `databricks` |
| Salesforce OAuth Credentials | `salesforce-oauth-credentials` | `salesforce` |

### SaaS and platforms

| Rotation | Type value | App Connection |
|----------|-----------|----------------|
| Cloudflare API Token | `cloudflare-api-token` | `cloudflare` |
| Cloudflare R2 Access Key | `cloudflare-r2-access-key` | `cloudflare` |
| Datadog API Key | `datadog-api-key` | `datadog` |
| Datadog Application Key | `datadog-application-key-secret` | `datadog` |
| Supabase API Key | `supabase-api-key` | `supabase` |
| Convex Access Key | `convex-access-key` | `convex` |
| DBT Service Token | `dbt-service-token` | `dbt` |

### LLM providers

| Rotation | Type value | App Connection |
|----------|-----------|----------------|
| OpenAI Service Account | `openai-service-account` | `openai` |
| OpenRouter API Key | `open-router-api-key` | `open-router` |
| LiteLLM API Key | `litellm-api-key` | `litellm` |
| Fireworks Secret | `fireworks-api-key` | `fireworks` |

### OS and hardware (all single-phase)

| Rotation | Type value | App Connection |
|----------|-----------|----------------|
| Unix/Linux Local Account | `unix-linux-local-account` | `ssh` |
| Windows Local Account | `windows-local-account` | `smb` |
| HP iLO Local Account | `hp-ilo-local-account` | `ssh` |

## Making applications pick up rotated values

Rotation changes the secret; it does not restart anything. Pair it with one of:

- **Infisical Agent** — template the secret to a file and use `execute.command` to reload the app on change (see `infisical-agent`)
- **Kubernetes Operator** — the operator updates the target Secret/ConfigMap; add a reloader or set the operator to trigger a rollout (see `infisical-kubernetes-operator`)
- **SDK with a short cache TTL** — must be well under 2× `rotationInterval`
- **CLI `infisical run`** — picks up current values at process start, so it benefits from a restart

An app that reads a secret once at boot and runs for months will break at the second rotation, not
the first. That surprises people.
