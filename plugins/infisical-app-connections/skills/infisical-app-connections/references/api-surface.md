<!-- GENERATED FILE — do not edit by hand.
     Source: tools/generate-app-connection-refs.py
     Regenerate: python3 tools/generate-app-connection-refs.py -->

# App Connection API Surface

Two distinct groups of endpoints, and the difference decides whether you can automate against them.

| Group | Count | Accepts a machine identity token? |
|---|---|---|
| Per-connection CRUD | 9 per connection | **8 of 9** — `/usage` is JWT-only |
| Resource-discovery endpoints | 94 total | **6 yes, 88 no** |

**88 of the 94 discovery endpoints are `AuthMode.JWT` only.** JWT means a
logged-in user session. A machine identity access token is rejected. Many of their router files
carry the comment *"The below endpoints are not exposed and for Infisical App use"* — they exist to
populate dropdowns in the Infisical UI, not as a public API.

Do not write automation against a JWT-only endpoint. See
[What to do instead](#what-to-do-instead-of-a-jwt-only-endpoint).

---

## Per-connection CRUD

Every connection type gets the same **nine** routes under `/api/v1/app-connections/<slug>`.
Eight accept a machine identity access token; `/usage` does not:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/` | identity + JWT | List connections of this type |
| `GET` | `/available` | identity + JWT | List connections usable in the caller's context |
| `GET` | `/{connectionId}` | identity + JWT | Get one by ID |
| `GET` | `/connection-name/{connectionName}` | identity + JWT | Get one **by name** |
| `POST` | `/` | identity + JWT | Create |
| `PATCH` | `/{connectionId}` | identity + JWT | Update |
| `DELETE` | `/{connectionId}` | identity + JWT | Delete |
| `POST` | `/{connectionId}/rotate-credentials` | identity + JWT | Rotate the connection's own stored credential |
| `GET` | `/{connectionId}/usage` | **JWT only** | What consumes this connection |

`GET /connection-name/{connectionName}` is the one worth knowing: it lets automation resolve a
connection by its stable name instead of storing a UUID.

`/usage` is JWT-only. To find what consumes a connection from automation, list the syncs, rotations,
and PKI syncs and filter by `connectionId`.

### Create

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/<slug>' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-aws",
    "method": "<one of the connection'"'"'s methods>",
    "credentials": { }
  }'
```

Per-connection `method` values and `credentials` fields:
[credentials-by-connection.md](./credentials-by-connection.md).

Optional body fields — several are hard errors on connections that do not support them:
`description` (max 256), `projectId`, `gatewayId`, `gatewayPoolId`,
`isPlatformManagedCredentials`, `isAutoRotationEnabled`, `rotation`.

---

## Discovery endpoints you can call programmatically

Only these **6** accept a machine identity access token.

| Connection | Endpoint | Returns | Query params |
|---|---|---|---|
| `adcs` | `GET /api/v1/app-connections/adcs/{connectionId}/certificate-templates` | `templates` | `caName` |
| `azure-adcs` | `GET /api/v1/app-connections/azure-adcs/{connectionId}/adcs-templates` | `templates` | — |
| `dbt` | `GET /api/v1/app-connections/dbt/{connectionId}/projects` | `projects` | — |
| `nutanix-prism-central` | `GET /api/v1/app-connections/nutanix-prism-central/{connectionId}/clusters` | `clusters` | — |
| `venafi` | `GET /api/v1/app-connections/venafi/{connectionId}/venafi-applications` | — | — |
| `venafi` | `GET /api/v1/app-connections/venafi/{connectionId}/venafi-issuing-templates` | — | `applicationId` |

---

## What to do instead of a JWT-only endpoint

You need a resource identifier — a vault ID, a repository slug, a cluster ID — to fill in a sync's
`destinationConfig` or a rotation's `parameters`. The Infisical endpoint that lists them is
UI-only. Three options, in order of preference:

1. **Ask the third-party provider directly.** The AWS SDK lists KMS keys; the Bitbucket API lists
   repositories; the 1Password CLI lists vaults. This is the correct automation path — Infisical is
   not the system of record for another provider's resources.
2. **Read the value out of the Infisical UI once** and commit it to your configuration. Resource
   IDs are stable; a vault ID does not change.
3. **Create the sync in the UI once**, then `GET` it through the API to see the exact
   `destinationConfig` the UI produced, and template your automation on that. This is the fastest
   way to get an unfamiliar destination config right.

Option 3 is usually the best answer when someone is stuck on an unfamiliar destination.

---

## All discovery endpoints

`identity` = callable with a machine identity token. `JWT only` = user session, UI-facing.

Each row also lists which features consume that connection, so you can see why the resource
matters.

### GitHub — `github`

Consumed by: Secret Sync: GitHub

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/environments` | **JWT only** | `environments` | `repo`, `owner` |
| `GET /{connectionId}/organizations` | **JWT only** | `organizations` | — |
| `GET /{connectionId}/repositories` | **JWT only** | `repositories` | — |

### GitHub Radar — `github-radar`

Consumed by: Scanning source: GitHub

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/repositories` | **JWT only** | `repositories` | — |

### AWS — `aws`

Consumed by: PKI Sync: AWS Certificate Manager, PKI Sync: AWS Elastic Load Balancer, PKI Sync: AWS Secrets Manager, Rotation: AWS IAM User Secret, Secret Sync: AWS Parameter Store, Secret Sync: AWS Secrets Manager

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/kms-keys` | **JWT only** | `kmsKeys` | `region`, `destination` |
| `GET /{connectionId}/users` | **JWT only** | `iamUsers` | — |

### Databricks — `databricks`

Consumed by: Rotation: Databricks Service Principal Secret, Secret Sync: Databricks

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/secret-scopes` | **JWT only** | `secretScopes` | — |
| `GET /{connectionId}/service-principals` | **JWT only** | `servicePrincipals` | — |

### GCP — `gcp`

Consumed by: Secret Sync: GCP Secret Manager

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/secret-manager-project-locations` | **JWT only** | `displayName`, `locationId` | `projectId` |
| `GET /{connectionId}/secret-manager-projects` | **JWT only** | `id`, `name` | — |

### Azure Client Secrets — `azure-client-secrets`

Consumed by: Rotation: Azure Client Secret

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/clients` | **JWT only** | `clients` | — |

### Azure DevOps — `azure-devops`

Consumed by: Secret Sync: Azure DevOps

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### Azure ADCS (Web Enrollment) — `azure-adcs`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/adcs-templates` | identity | `templates` | — |

### Microsoft ADCS — `adcs`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/certificate-templates` | identity | `templates` | `caName` |

### Azure DNS — `azure-dns`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/azure-dns-zones` | **JWT only** | — | — |

### Humanitec — `humanitec`

Consumed by: Secret Sync: Humanitec

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/organizations` | **JWT only** | — | — |

### Vercel — `vercel`

Consumed by: Secret Sync: Vercel

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | — | `projectSearch` |

### Camunda — `camunda`

Consumed by: Secret Sync: Camunda

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/clusters` | **JWT only** | `clusters` | — |

### Windmill — `windmill`

Consumed by: Secret Sync: Windmill

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/workspaces` | **JWT only** | — | — |

### Auth0 — `auth0`

Consumed by: Rotation: Auth0 Client Secret

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/clients` | **JWT only** | `clients` | — |

### TeamCity — `teamcity`

Consumed by: Secret Sync: TeamCity

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | — | — |

### OCI — `oci`

Consumed by: Secret Sync: OCI Vault

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/compartments` | **JWT only** | — | — |
| `GET /{connectionId}/vault-keys` | **JWT only** | — | `compartmentOcid`, `vaultOcid` |
| `GET /{connectionId}/vaults` | **JWT only** | — | `compartmentOcid` |

### 1Password — `1password`

Consumed by: Secret Sync: 1Password

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/vaults` | **JWT only** | — | — |

### Heroku — `heroku`

Consumed by: Secret Sync: Heroku

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/apps` | **JWT only** | — | — |

### Render — `render`

Consumed by: Secret Sync: Render

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/environment-groups` | **JWT only** | — | — |
| `GET /{connectionId}/services` | **JWT only** | — | — |

### Fly.io — `flyio`

Consumed by: Secret Sync: Fly.io

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/apps` | **JWT only** | — | — |

### Trigger.dev — `trigger-dev`

Consumed by: Secret Sync: Trigger.dev

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/environments` | **JWT only** | — | `projectRef` |
| `GET /{connectionId}/projects` | **JWT only** | — | — |

### GitLab — `gitlab`

Consumed by: Scanning source: GitLab, Secret Sync: GitLab

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/groups` | **JWT only** | — | `search`, `limit` |
| `GET /{connectionId}/projects` | **JWT only** | — | `search`, `limit` |

### Cloudflare — `cloudflare`

Consumed by: PKI Sync: Cloudflare Custom SSL Certificate, Rotation: Cloudflare API Token, Rotation: Cloudflare R2 Access Key, Secret Sync: Cloudflare Pages, Secret Sync: Cloudflare Workers

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/cloudflare-pages-projects` | **JWT only** | — | — |
| `GET /{connectionId}/cloudflare-permission-groups` | **JWT only** | — | — |
| `GET /{connectionId}/cloudflare-r2-buckets` | **JWT only** | — | — |
| `GET /{connectionId}/cloudflare-workers-scripts` | **JWT only** | — | — |
| `GET /{connectionId}/cloudflare-zones` | **JWT only** | — | — |

### DNS Made Easy — `dns-made-easy`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/dns-made-easy-zones` | **JWT only** | — | — |

### Zabbix — `zabbix`

Consumed by: Secret Sync: Zabbix

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/hosts` | **JWT only** | — | — |

### Railway — `railway`

Consumed by: Secret Sync: Railway

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### Bitbucket — `bitbucket`

Consumed by: Scanning source: Bitbucket, Secret Sync: Bitbucket

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/environments` | **JWT only** | `environments` | `workspaceSlug`, `repositorySlug` |
| `GET /{connectionId}/repositories` | **JWT only** | `repositories` | `workspaceSlug`, `search` |
| `GET /{connectionId}/workspaces` | **JWT only** | `workspaces` | `search` |

### Checkly — `checkly`

Consumed by: Secret Sync: Checkly

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/accounts` | **JWT only** | `accounts` | — |
| `GET /{connectionId}/accounts/:accountId/groups` | **JWT only** | `groups` | — |

### Supabase — `supabase`

Consumed by: Rotation: Supabase API Key, Secret Sync: Supabase

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### DigitalOcean App Platform — `digital-ocean`

Consumed by: Secret Sync: Digital Ocean App Platform

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/apps` | **JWT only** | `apps` | — |

### Netlify — `netlify`

Consumed by: Secret Sync: Netlify

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/accounts` | **JWT only** | `accounts` | — |
| `GET /{connectionId}/accounts/:accountId/sites` | **JWT only** | `sites` | — |

### Okta — `okta`

Consumed by: Rotation: Okta Client Secret

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/apps` | **JWT only** | `apps` | — |

### Laravel Forge — `laravel-forge`

Consumed by: Secret Sync: Laravel Forge

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/organizations` | **JWT only** | — | — |
| `GET /{connectionId}/servers` | **JWT only** | — | `organizationSlug` |
| `GET /{connectionId}/sites` | **JWT only** | — | `organizationSlug`, `serverId` |

### Chef — `chef`

Consumed by: PKI Sync: Chef, Secret Sync: Chef

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/data-bag-items` | **JWT only** | — | `dataBagName` |
| `GET /{connectionId}/data-bags` | **JWT only** | — | — |

### Northflank — `northflank`

Consumed by: Secret Sync: Northflank

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |
| `GET /{connectionId}/projects/:projectId/secret-groups` | **JWT only** | `secretGroups` | — |

### Octopus Deploy — `octopus-deploy`

Consumed by: Secret Sync: Octopus Deploy

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | — | `spaceId` |
| `GET /{connectionId}/scope-values` | **JWT only** | `environments`, `roles`, `machines`, `processes`, `actions`, `channels` | `spaceId`, `projectId` |
| `GET /{connectionId}/spaces` | **JWT only** | — | — |

### DBT — `dbt`

Consumed by: Rotation: DBT Service Token

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | identity | `projects` | — |

### OpenAI — `openai`

Consumed by: Rotation: OpenAI Service Account

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### CircleCI — `circleci`

Consumed by: Secret Sync: CircleCI

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `organizations` | — |

### Azure Entra ID — `azure-entra-id`

Consumed by: Secret Sync: Azure Entra ID SCIM

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/scim-service-principals` | **JWT only** | `servicePrincipals` | `search` |

### Venafi TLS Protect Cloud — `venafi`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/venafi-applications` | identity | — | — |
| `GET /{connectionId}/venafi-issuing-templates` | identity | — | `applicationId` |

### Infisical — `external-infisical`

Consumed by: Secret Sync: Infisical

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |
| `GET /{connectionId}/projects/:projectId/environment-folder-tree` | **JWT only** | — | — |

### Ona — `ona`

Consumed by: Secret Sync: Ona

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | — | — |

### DigiCert — `digicert`

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/organizations` | **JWT only** | — | — |
| `GET /{connectionId}/organizations/:organizationId/orders` | **JWT only** | — | `productNameId` |
| `GET /{connectionId}/organizations/:organizationId/validation` | **JWT only** | `isValidated` | `productNameId` |
| `GET /{connectionId}/products` | **JWT only** | — | — |

### Travis CI — `travis-ci`

Consumed by: Secret Sync: Travis CI

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/branches` | **JWT only** | — | `repositoryId` |
| `GET /{connectionId}/repositories` | **JWT only** | — | — |

### Salesforce — `salesforce`

Consumed by: Rotation: Salesforce OAuth Credentials

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/oauth-apps` | **JWT only** | `apps` | — |

### Snowflake — `snowflake`

Consumed by: Rotation: Snowflake User Key Pair, Secret Sync: Snowflake

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/databases` | **JWT only** | `databases` | — |
| `GET /{connectionId}/schemas` | **JWT only** | `schemas` | `database` |
| `GET /{connectionId}/users` | **JWT only** | `users` | — |

### Datadog — `datadog`

Consumed by: Rotation: Datadog API Key, Rotation: Datadog Application Key

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/service-accounts` | **JWT only** | `serviceAccounts` | — |

### Rundeck — `rundeck`

Consumed by: Secret Sync: Rundeck

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### Hasura Cloud — `hasura-cloud`

Consumed by: Secret Sync: Hasura Cloud

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/projects` | **JWT only** | `projects` | — |

### Qovery — `qovery`

Consumed by: Secret Sync: Qovery

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/organizations` | **JWT only** | — | — |
| `GET /{connectionId}/organizations/:organizationId/projects` | **JWT only** | — | — |
| `GET /{connectionId}/projects/:projectId/environments` | **JWT only** | — | — |

### Cloud 66 — `cloud-66`

Consumed by: Secret Sync: Cloud 66

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/stacks` | **JWT only** | — | — |

### LiteLLM — `litellm`

Consumed by: Rotation: LiteLLM API Key

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/models` | **JWT only** | `models` | — |
| `GET /{connectionId}/teams` | **JWT only** | `teams` | `search` |
| `GET /{connectionId}/users` | **JWT only** | `users` | `search` |

### Fireworks — `fireworks`

Consumed by: Rotation: Fireworks Secret

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/service-accounts` | **JWT only** | `serviceAccounts` | — |

### Nutanix Prism Central — `nutanix-prism-central`

Consumed by: PKI Sync: Nutanix Prism Central

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/clusters` | identity | `clusters` | — |

### Spacelift — `spacelift`

Consumed by: Secret Sync: Spacelift

| Endpoint | Auth | Returns | Query params |
|---|---|---|---|
| `GET /{connectionId}/contexts` | **JWT only** | — | — |

### Connections with no discovery endpoints (26)

`azure-key-vault`, `azure-app-configuration`, `terraform-cloud`, `postgres`, `mssql`, `mysql`, `hashicorp-vault`, `ldap`, `oracledb`, `redis`, `mongodb`, `ssh`, `smb`, `winrm`, `open-router`, `venafi-tpp`, `doppler`, `netscaler`, `anthropic`, `ovh`, `devin`, `f5-big-ip`, `godaddy`, `convex`, `kemp-loadmaster`, `microsoft-intune`

For these, every value in a consumer's config comes from you or from the provider.
