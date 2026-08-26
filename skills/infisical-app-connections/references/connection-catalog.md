# App Connection Catalog

All **83** App Connection types, with the exact `method` values each accepts.

## Reading this table

- **Slug** is the `app` value and the URL segment: `POST /api/v1/app-connections/<slug>`
- **Auth methods** are the exact `method` values. These are validated strings — `access-keys` or `github_app` are rejected
- **Flags**:
  - `GW` — accepts `gatewayId` or `gatewayPoolId` for private-network routing (16 connections)
  - `PM` — supports `isPlatformManagedCredentials` (3 connections)
  - `CR` — supports connection-level credential rotation (5 connections)
- "see docs" means the connection does not expose a discrete method enum; its credentials are supplied directly in the create body. Check the per-connection page under `docs/integrations/app-connections/`

## The catalog

| Connection | Slug | Auth methods | Flags |
|---|---|---|---|
| GitHub | `github` | `oauth`, `github-app`, `pat` | GW |
| GitHub Radar | `github-radar` | `github-app` | — |
| AWS | `aws` | `assume-role`, `access-key` | — |
| Databricks | `databricks` | `service-principal` | — |
| GCP | `gcp` | `service-account-impersonation` | — |
| Azure Key Vault | `azure-key-vault` | `oauth`, `client-secret`, `certificate` | GW CR |
| Azure App Configuration | `azure-app-configuration` | `oauth`, `client-secret` | CR |
| Azure Client Secrets | `azure-client-secrets` | `oauth`, `client-secret`, `certificate` | CR |
| Azure DevOps | `azure-devops` | see docs | — |
| Azure ADCS (Web Enrollment) | `azure-adcs` | `username-password` | — |
| Microsoft ADCS | `adcs` | `username-password` | GW |
| Azure DNS | `azure-dns` | `client-secret` | — |
| Humanitec | `humanitec` | `api-token` | — |
| Terraform Cloud | `terraform-cloud` | `api-token` | — |
| Vercel | `vercel` | `api-token` | — |
| PostgreSQL | `postgres` | `username-and-password` | GW PM |
| Microsoft SQL Server | `mssql` | `username-and-password` | GW PM |
| MySQL | `mysql` | `username-and-password` | GW PM |
| Camunda | `camunda` | `client-credentials` | — |
| Windmill | `windmill` | `access-token` | — |
| Auth0 | `auth0` | `client-credentials` | — |
| Hashicorp Vault | `hashicorp-vault` | see docs | GW |
| LDAP | `ldap` | `simple-bind` | GW CR |
| TeamCity | `teamcity` | `access-token` | — |
| OCI | `oci` | see docs | — |
| OracleDB | `oracledb` | see docs | — |
| 1Password | `1password` | `api-token` | — |
| Heroku | `heroku` | `auth-token`, `oauth` | — |
| Render | `render` | `api-key` | — |
| Fly.io | `flyio` | `access-token` | — |
| Trigger.dev | `trigger-dev` | `api-key` | — |
| GitLab | `gitlab` | `oauth`, `access-token` | — |
| Cloudflare | `cloudflare` | see docs | — |
| DNS Made Easy | `dns-made-easy` | see docs | — |
| Zabbix | `zabbix` | `api-token` | — |
| Railway | `railway` | see docs | — |
| Bitbucket | `bitbucket` | `api-token` | — |
| Checkly | `checkly` | see docs | — |
| Supabase | `supabase` | see docs | — |
| DigitalOcean App Platform | `digital-ocean` | see docs | — |
| Netlify | `netlify` | see docs | — |
| Okta | `okta` | `api-token` | — |
| Redis | `redis` | `username-and-password` | — |
| MongoDB | `mongodb` | `username-and-password` | — |
| Laravel Forge | `laravel-forge` | `api-token` | — |
| Chef | `chef` | see docs | — |
| Northflank | `northflank` | `api-token` | — |
| Octopus Deploy | `octopus-deploy` | `api-key` | — |
| SSH | `ssh` | `password`, `ssh-key` | GW |
| DBT | `dbt` | see docs | — |
| Windows (SMB) | `smb` | `credentials` | GW |
| Windows (WinRM) | `winrm` | `username-password` | GW |
| OpenRouter | `open-router` | `api-key` | — |
| OpenAI | `openai` | `api-key` | — |
| CircleCI | `circleci` | `api-token` | — |
| Azure Entra ID | `azure-entra-id` | `client-secret` | CR |
| Venafi TLS Protect Cloud | `venafi` | `api-key` | — |
| Venafi TPP | `venafi-tpp` | `oauth` | GW |
| Infisical | `external-infisical` | `machine-identity-universal-auth` | — |
| Doppler | `doppler` | `api-token` | — |
| NetScaler | `netscaler` | `basic-auth` | GW |
| Anthropic | `anthropic` | `api-key` | — |
| OVH | `ovh` | `certificate` | — |
| Devin | `devin` | `api-key` | — |
| Ona | `ona` | `personal-access-token` | — |
| DigiCert | `digicert` | `api-key` | — |
| Travis CI | `travis-ci` | `api-token` | — |
| Salesforce | `salesforce` | `client-credentials` | — |
| Snowflake | `snowflake` | `username-and-token` | — |
| Datadog | `datadog` | `token`, `api-key` | — |
| F5 BIG-IP | `f5-big-ip` | `basic-auth` | GW |
| GoDaddy | `godaddy` | `api-key` | — |
| Convex | `convex` | `personal-access-token` | — |
| Rundeck | `rundeck` | `api-token` | — |
| Hasura Cloud | `hasura-cloud` | `access-token` | — |
| Qovery | `qovery` | `access-token` | — |
| Cloud 66 | `cloud-66` | `access-token` | — |
| LiteLLM | `litellm` | `api-key` | — |
| Fireworks | `fireworks` | `api-key` | — |
| Kemp LoadMaster | `kemp-loadmaster` | `basic-auth` | GW |
| Microsoft Intune | `microsoft-intune` | `client-secret` | — |
| Nutanix Prism Central | `nutanix-prism-central` | `api-key`, `basic-auth` | GW |
| Spacelift | `spacelift` | `api-key-secret` | — |

## Auth method vocabulary

The same concept goes by different strings on different connections. Do not generalize — check the
row above.

| Value | Used by | Meaning |
|-------|---------|---------|
| `api-key` | 14 connections | A static API key |
| `api-token` | 13 connections | A static API token |
| `oauth` | 7 connections | Browser OAuth flow from the Infisical UI |
| `access-token` | 7 connections | A static access token |
| `client-secret` | 6 connections | OAuth client credentials (Azure-style app registration) |
| `username-and-password` | Postgres, MSSQL, MySQL, Redis, MongoDB | Database login |
| `username-password` | Azure ADCS, Microsoft ADCS, WinRM | Note: **no `and`** in this variant |
| `basic-auth` | NetScaler, F5 BIG-IP, Kemp LoadMaster, Nutanix | HTTP basic auth |
| `certificate` | Azure Key Vault, Azure Client Secrets, OVH | Client certificate |
| `client-credentials` | Camunda, Auth0, Salesforce | OAuth client-credentials grant |
| `assume-role` / `access-key` | AWS only | IAM role assumption vs static keys |
| `service-account-impersonation` | GCP only | The only GCP method |
| `github-app` / `oauth` / `pat` | GitHub | GitHub App install, OAuth, or personal access token |
| `service-principal` | Databricks | Databricks service principal |
| `simple-bind` | LDAP | LDAP simple bind |
| `password` / `ssh-key` | SSH | Password or key-based SSH |
| `credentials` | SMB | Windows credentials |
| `machine-identity-universal-auth` | External Infisical | Universal Auth against another Infisical instance |
| `username-and-token` | Snowflake | Username plus token |
| `personal-access-token` | Ona, Convex | A personal access token |
| `api-key-secret` | Spacelift | API key ID plus secret |
| `auth-token` | Heroku | Heroku auth token |
| `token` | Datadog | Datadog token |

Watch `username-and-password` versus `username-password`. Databases use the first; ADCS and WinRM
use the second. This trips people up because the two look interchangeable and are not.

## Creating a connection

```
POST /api/v1/app-connections/<slug>
```

Common body fields, regardless of connection type:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Slug-formatted name, unique in the org |
| `method` | Yes | One of the connection's auth methods (see table) |
| `credentials` | Yes | Method-specific credential object |
| `description` | No | Max 256 characters |
| `projectId` | No | Scope the connection to one project instead of the whole org |
| `gatewayId` | Only if `GW` | Route through a specific Gateway |
| `gatewayPoolId` | Only if `GW` | Route through a Gateway pool |
| `isPlatformManagedCredentials` | Only if `PM` | Let Infisical own and rotate the credential |
| `isAutoRotationEnabled` | Only if `CR` | Enable connection credential rotation |
| `rotation` | Required when `isAutoRotationEnabled` | Rotation config for the connection's own credential |

Example — AWS with role assumption:

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/aws' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-aws",
    "method": "assume-role",
    "description": "Used by secrets-manager syncs in prod",
    "credentials": {
      "roleArn": "arn:aws:iam::123456789012:role/InfisicalSecretsManager"
    }
  }'
```

The response includes the connection's `id` (a UUID). That is the `connectionId` you pass to a
sync, rotation, PKI sync, or scanning data source.

## Validation errors worth recognizing

| Error | Cause |
|-------|-------|
| `Not supported for <Name> Connections` | You passed `gatewayId`, `gatewayPoolId`, `isPlatformManagedCredentials`, or `rotation` to a connection that does not support it. These are hard errors, not ignored fields |
| `Cannot specify both a gateway and a gateway pool` | `gatewayId` and `gatewayPoolId` are mutually exclusive — pick one |
| `Rotation details is required when auto rotation is enabled` | `isAutoRotationEnabled: true` without a `rotation` object |
| Invalid enum value for `method` | The method string is wrong for this connection type |

## Connection-level credential rotation

Five connections can rotate the credential **they themselves store**:
`azure-app-configuration`, `azure-client-secrets`, `azure-entra-id`, `azure-key-vault`, `ldap`.

```json
{
  "isAutoRotationEnabled": true,
  "rotation": {
    "rotationInterval": 30,
    "rotateAtUtc": { "hours": 2, "minutes": 0 }
  }
}
```

This keeps Infisical's own stored credential fresh. It writes **nothing** into your project
secrets. If the user wants rotated values landing in secrets that applications read, that is
Secret Rotation — see `infisical-secret-rotation`. The two features share vocabulary
(`rotationInterval`, `rotateAtUtc`) and are otherwise unrelated.

The connection object also exposes read-only rotation state: `lastRotationMessage`,
`nextRotationAt`, and `rotationStatus`.

## Platform-managed credentials

`postgres`, `mysql`, and `mssql` support `isPlatformManagedCredentials: true`, which hands
ownership of the database credential to Infisical. Infisical then manages that password itself
rather than relying on one you keep in sync by hand.

Do not enable this on a shared account that humans or other systems also use — Infisical will
change the password out from under them.
