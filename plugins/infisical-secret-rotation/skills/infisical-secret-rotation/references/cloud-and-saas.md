# Rotation: Cloud, Identity, and SaaS Providers

All providers on this page are **dual-phase** (zero-downtime) unless marked otherwise.

For each, `parameters` says *what to rotate* and `secretsMapping` says *which Infisical secret
names receive the rotated values*. Every field in a provider's `secretsMapping` is a secret name
you choose.

## Cloud and identity

### AWS IAM User Secret — `aws-iam-user-secret`

App Connection: `aws`

| `parameters` | Description |
|--------------|-------------|
| `userName` | The IAM user whose access key is rotated |
| `region` | AWS region |

| `secretsMapping` | Receives |
|------------------|----------|
| `accessKeyId` | The active access key ID |
| `secretAccessKey` | The active secret access key |

The IAM user must already exist. AWS permits two access keys per user simultaneously, which is
what makes this dual-phase. If the user already has two keys, rotation cannot create a third —
delete one first.

### Azure Client Secret — `azure-client-secret`

App Connection: `azure-client-secrets`

| `parameters` | Description |
|--------------|-------------|
| `objectId` | Object ID of the Azure application |
| `appName` | Name of the Azure application |
| `clientId` | Client ID of the application |

| `secretsMapping` | Receives |
|------------------|----------|
| `clientId` | The application's client ID |
| `clientSecret` | The rotated client secret |

Note `clientId` appears in both — it is supplied as a parameter (to identify the app) and mapped
out (so consumers can read it alongside the secret).

### Okta Client Secret — `okta-client-secret`

App Connection: `okta`

| `parameters` | `clientId` — the Okta application to rotate |
| `secretsMapping` | `clientId`, `clientSecret` |

### Auth0 Client Secret — `auth0-client-secret` — **SINGLE-PHASE**

App Connection: `auth0`

| `parameters` | `clientId` — the Auth0 application |
| `secretsMapping` | `clientId`, `clientSecret` |

**Old secret is invalidated immediately.** Auth0 only supports one active client secret per
application. Disable auto-rotation and rotate during a maintenance window.

### Databricks Service Principal Secret — `databricks-service-principal-secret`

App Connection: `databricks`

| `parameters` | Description |
|--------------|-------------|
| `servicePrincipalId` | The service principal to rotate |
| `servicePrincipalName` | Its display name |
| `clientId` | Client ID |

| `secretsMapping` | `clientId`, `clientSecret` |

### Salesforce OAuth Credentials — `salesforce-oauth-credentials`

App Connection: `salesforce`

| `parameters` | `appId`, `appName` |
| `secretsMapping` | `consumerKey`, `consumerSecret` |

Note Salesforce's terminology: consumer key/secret rather than client ID/secret.

### Snowflake User Key Pair — `snowflake-user-key-pair`

App Connection: `snowflake`

| `parameters` | Description |
|--------------|-------------|
| `username` | The Snowflake user configured for key-pair auth |
| `modulusLength` | RSA key size |

| `secretsMapping` | Receives |
|------------------|----------|
| `privateKey` | The active RSA private key |
| `publicKey` | The corresponding public key |

This rotates an **RSA key pair**, not a password. Snowflake supports two registered public keys
per user (`RSA_PUBLIC_KEY` and `RSA_PUBLIC_KEY_2`), which is what enables dual-phase. The user must
already be configured for key-pair authentication.

## SaaS and platforms

### Cloudflare API Token — `cloudflare-api-token`

App Connection: `cloudflare`

| `parameters` | Description |
|--------------|-------------|
| `name` | Name given to the generated token |
| `policies` | Permission policies attached to the token |
| `allowedIps` | Optional IP allowlist |
| `disallowedIps` | Optional IP denylist |

| `secretsMapping` | `tokenId`, `apiToken` |

Infisical **creates and destroys tokens** here rather than changing one token's value, so
`policies` defines what each generated token can do.

### Cloudflare R2 Access Key — `cloudflare-r2-access-key`

App Connection: `cloudflare`

| `parameters` | Description |
|--------------|-------------|
| `name` | Name for the generated key |
| `buckets` | Buckets the key may access |
| `accessLevel` | Access level granted |
| `allowedIps` / `disallowedIps` | Optional IP restrictions |

| `secretsMapping` | `accessKeyId`, `secretAccessKey` |

### Datadog API Key — `datadog-api-key`

App Connection: `datadog`

| `parameters` | `name` — name for the generated key |
| `secretsMapping` | `apiKeyId`, `apiKey` |

### Datadog Application Key — `datadog-application-key-secret`

App Connection: `datadog`

| `parameters` | `serviceAccountId` — the service account owning the key |
| `secretsMapping` | `applicationKeyId`, `applicationKey` |

Datadog distinguishes API keys (org-level ingestion) from Application keys (scoped to a user or
service account, used for the API). They are separate rotation types — pick based on which your
integration uses.

### Supabase API Key — `supabase-api-key`

App Connection: `supabase`

| `parameters` | Description |
|--------------|-------------|
| `projectRef` | Supabase project reference |
| `keyType` | Which key type to rotate |

| `secretsMapping` | `apiKey` |

### Convex Access Key — `convex-access-key`

App Connection: `convex`

| `parameters` | `namePrefix` — prefix for generated key names |
| `secretsMapping` | `accessKey` |

### DBT Service Token — `dbt-service-token`

App Connection: `dbt`

| `parameters` | Description |
|--------------|-------------|
| `tokenName` | Name for the generated service token |
| `permissionGrants` | Permissions attached to the token |

| `secretsMapping` | `serviceToken` |

## LLM provider keys

These follow a common shape: Infisical creates a new API key, maps it to a secret, and destroys
the superseded one on the following rotation.

### OpenAI Service Account — `openai-service-account`

App Connection: `openai`

| `parameters` | `projectId`, `name` |
| `secretsMapping` | `apiKey` |

Rotates a service-account API key within an OpenAI project.

### OpenRouter API Key — `open-router-api-key`

App Connection: `open-router`

| `parameters` | Description |
|--------------|-------------|
| `name` | Name for the generated key |
| `limit` | Spend limit on the key |
| `limitReset` | How the limit resets |
| `includeByokInLimit` | Whether bring-your-own-key usage counts toward the limit |

| `secretsMapping` | `apiKey` |

Useful pattern: a low `limit` on a rotated key bounds the damage from a leak in both directions —
the key expires *and* it can only spend so much.

### LiteLLM API Key — `litellm-api-key`

App Connection: `litellm`

| `parameters` | Description |
|--------------|-------------|
| `name` | Name for the generated key |
| `userId` | LiteLLM user to associate |
| `teamId` | LiteLLM team to associate |
| `models` | Models the key may call |
| `additionalOptions` | Further LiteLLM key options |

| `secretsMapping` | `apiKey` |

### Fireworks Secret — `fireworks-api-key`

App Connection: `fireworks`

| `parameters` | `serviceAccountUserId` |
| `secretsMapping` | `apiKey` |

## Choosing an interval

| Credential kind | Suggested `rotationInterval` |
|-----------------|------------------------------|
| Production database passwords | 30 days |
| Cloud provider access keys | 30–90 days |
| LLM / SaaS API keys | 30 days, or shorter with spend limits |
| Anything single-phase | Manual, with auto-rotation disabled |

Shorter is not automatically better. Each rotation is a chance for a consumer to be caught
holding a stale value, so match the interval to how quickly your applications re-read secrets.
