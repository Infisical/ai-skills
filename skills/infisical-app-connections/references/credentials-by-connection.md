<!-- GENERATED FILE — do not edit by hand.
     Source: tools/generate-app-connection-refs.py
     Regenerate: python3 tools/generate-app-connection-refs.py -->

# Credential Fields by Connection

Every one of the **83** App Connection types, with the exact `method` values it accepts and the `credentials` fields each method requires.

`POST /api/v1/app-connections/<slug>` with body `{ name, method, credentials: { ... } }`. See [api-surface.md](./api-surface.md) for the full request shape.

| Notation | Meaning |
|---|---|
| **`bold`** | Required |
| `plain` | Optional — has `.optional()`, `.nullish()`, or a default |
| `plain`¹ | **Conditional** — required in some variants of the schema only |

¹ A conditional field is required by one branch of a union and optional in another. The clearest case is GitHub: `host` is required when `instanceType` is `server` and optional when it is `cloud`. Read the connection's own page under `docs/integrations/app-connections/` before assuming which applies.

Where a method shows *(see per-connection docs)*, the schema could not be resolved mechanically — check `docs/integrations/app-connections/<slug>` rather than guessing.

---

## GitHub — `github`

| `method` | `credentials` fields |
|---|---|
| `github-app` | **`code`**, **`installationId`**, `gitHubAppId`, `instanceType`¹, `host`¹ |
| `oauth` | **`code`**, `instanceType`¹, `host`¹ |
| `pat` | **`personalAccessToken`**, `instanceType`¹, `host`¹ |

## GitHub Radar — `github-radar`

| `method` | `credentials` fields |
|---|---|
| `github-app` | **`code`**, **`installationId`** |

## AWS — `aws`

| `method` | `credentials` fields |
|---|---|
| `assume-role` | **`roleArn`**, `stsEndpoint` |
| `access-key` | **`accessKeyId`**, **`secretAccessKey`** |

## Databricks — `databricks`

| `method` | `credentials` fields |
|---|---|
| `service-principal` | **`clientId`**, **`clientSecret`**, **`workspaceUrl`** |

## GCP — `gcp`

| `method` | `credentials` fields |
|---|---|
| `service-account-impersonation` | **`serviceAccountEmail`** |

## Azure Key Vault — `azure-key-vault`

| `method` | `credentials` fields |
|---|---|
| `oauth` | **`code`**, `tenantId` |
| `client-secret` | **`clientId`**, **`clientSecret`**, **`tenantId`**, `clientSecretKeyId` |
| `certificate` | **`tenantId`**, **`clientId`**, **`certificateBody`**, **`privateKey`** |

## Azure App Configuration — `azure-app-configuration`

| `method` | `credentials` fields |
|---|---|
| `oauth` | **`code`**, `tenantId` |
| `client-secret` | **`clientId`**, **`clientSecret`**, **`tenantId`**, `clientSecretKeyId` |

## Azure Client Secrets — `azure-client-secrets`

| `method` | `credentials` fields |
|---|---|
| `oauth` | **`code`**, **`tenantId`** |
| `client-secret` | **`clientId`**, **`clientSecret`**, **`tenantId`**, `clientSecretKeyId` |
| `certificate` | **`tenantId`**, **`clientId`**, **`certificateBody`**, **`privateKey`** |

## Azure DevOps — `azure-devops`

| `method` | `credentials` fields |
|---|---|
| `oauth` | **`code`**, **`tenantId`**, **`orgName`** |
| `access-token` | **`accessToken`**, **`orgName`** |
| `client-secret` | **`clientId`**, **`clientSecret`**, **`tenantId`**, **`orgName`**, `clientSecretKeyId` |

## Azure ADCS (Web Enrollment) — `azure-adcs`

| `method` | `credentials` fields |
|---|---|
| `username-password` | **`adcsUrl`**, **`username`**, **`password`**, `sslRejectUnauthorized`, `sslCertificate` |

## Microsoft ADCS — `adcs`

| `method` | `credentials` fields |
|---|---|
| `username-password` | **`host`**, **`username`**, **`password`** |

## Azure DNS — `azure-dns`

| `method` | `credentials` fields |
|---|---|
| `client-secret` | **`tenantId`**, **`clientId`**, **`clientSecret`**, **`subscriptionId`**, `clientSecretKeyId` |

## Humanitec — `humanitec`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## Terraform Cloud — `terraform-cloud`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## Vercel — `vercel`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## PostgreSQL — `postgres`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`database`**, **`username`**, **`password`**, **`sslEnabled`**, **`sslRejectUnauthorized`**, `sslCertificate` |

## Microsoft SQL Server — `mssql`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`database`**, **`username`**, **`password`**, **`sslEnabled`**, **`sslRejectUnauthorized`**, `sslCertificate` |

## MySQL — `mysql`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`database`**, **`username`**, **`password`**, **`sslEnabled`**, **`sslRejectUnauthorized`**, `sslCertificate` |

## Camunda — `camunda`

| `method` | `credentials` fields |
|---|---|
| `client-credentials` | **`clientId`**, **`clientSecret`** |

## Windmill — `windmill`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`**, `instanceUrl` |

## Auth0 — `auth0`

| `method` | `credentials` fields |
|---|---|
| `client-credentials` | **`domain`**, **`clientId`**, **`clientSecret`**, **`audience`** |

## Hashicorp Vault — `hashicorp-vault`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`instanceUrl`**, **`namespace`**, **`accessToken`** |
| `app-role` | **`instanceUrl`**, **`namespace`**, **`roleId`**, **`secretId`** |

## LDAP — `ldap`

| `method` | `credentials` fields |
|---|---|
| `simple-bind` | **`provider`**, **`url`**, **`dn`**, **`password`**, `sslRejectUnauthorized`, `sslCertificate` |

## TeamCity — `teamcity`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`**, **`instanceUrl`** |

## OCI — `oci`

| `method` | `credentials` fields |
|---|---|
| `access-key` | **`userOcid`**, **`tenancyOcid`**, **`region`**, **`fingerprint`**, **`privateKey`** |

## OracleDB — `oracledb`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`database`**, **`username`**, **`password`**, **`sslEnabled`**, **`sslRejectUnauthorized`**, `sslCertificate` |

## 1Password — `1password`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`**, **`instanceUrl`** |

## Heroku — `heroku`

| `method` | `credentials` fields |
|---|---|
| `auth-token` | **`authToken`** |
| `oauth` | *(see per-connection docs)* |

## Render — `render`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`** |

## Fly.io — `flyio`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`** |

## Trigger.dev — `trigger-dev`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`**, `instanceUrl` |

## GitLab — `gitlab`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`**, `instanceUrl`, **`accessTokenType`** |
| `oauth` | *(see per-connection docs)* |

## Cloudflare — `cloudflare`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`accountId`**, **`apiToken`** |

## DNS Made Easy — `dns-made-easy`

| `method` | `credentials` fields |
|---|---|
| `api-key-secret` | **`apiKey`**, **`secretKey`** |

## Zabbix — `zabbix`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`**, **`instanceUrl`** |

## Railway — `railway`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`apiToken`** |

## Bitbucket — `bitbucket`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`**, **`email`** |

## Checkly — `checkly`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`apiKey`** |

## Supabase — `supabase`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`accessKey`**, `instanceUrl` |

## DigitalOcean App Platform — `digital-ocean`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`apiToken`** |

## Netlify — `netlify`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`accessToken`** |

## Okta — `okta`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`instanceUrl`**, **`apiToken`** |

## Redis — `redis`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`username`**, `password`, **`sslRejectUnauthorized`**, **`sslEnabled`**, `sslCertificate` |

## MongoDB — `mongodb`

| `method` | `credentials` fields |
|---|---|
| `username-and-password` | **`host`**, **`port`**, **`username`**, **`password`**, **`database`**, **`tlsRejectUnauthorized`**, **`tlsEnabled`**, `tlsCertificate` |

## Laravel Forge — `laravel-forge`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## Chef — `chef`

| `method` | `credentials` fields |
|---|---|
| `user-key` | `serverUrl`, **`orgName`**, **`userName`**, **`privateKey`** |

## Northflank — `northflank`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## Octopus Deploy — `octopus-deploy`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`instanceUrl`**, **`apiKey`** |

## SSH — `ssh`

| `method` | `credentials` fields |
|---|---|
| `password` | **`host`**, **`port`**, **`username`**, **`password`** |
| `ssh-key` | **`host`**, **`port`**, **`username`**, **`privateKey`**, `passphrase` |

## DBT — `dbt`

| `method` | `credentials` fields |
|---|---|
| `(see docs)` | **`apiToken`**, **`instanceUrl`**, **`accountId`** |

## Windows (SMB) — `smb`

| `method` | `credentials` fields |
|---|---|
| `credentials` | **`host`**, **`port`**, `domain`, **`username`**, **`password`** |

## Windows (WinRM) — `winrm`

| `method` | `credentials` fields |
|---|---|
| `username-password` | **`host`**, `port`, **`username`**, **`password`**, `sslEnabled`, `sslRejectUnauthorized`, `sslCertificate` |

## OpenRouter — `open-router`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`** |

## OpenAI — `openai`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`** |

## CircleCI — `circleci`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`**, `host` |

## Azure Entra ID — `azure-entra-id`

| `method` | `credentials` fields |
|---|---|
| `client-secret` | **`clientId`**, **`clientSecret`**, **`tenantId`**, `clientSecretKeyId` |

## Venafi TLS Protect Cloud — `venafi`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`**, **`region`** |

## Venafi TPP — `venafi-tpp`

| `method` | `credentials` fields |
|---|---|
| `oauth` | **`tppUrl`**, **`clientId`**, **`username`**, **`password`** |

## Infisical — `external-infisical`

| `method` | `credentials` fields |
|---|---|
| `machine-identity-universal-auth` | **`instanceUrl`**, **`machineIdentityClientId`**, **`machineIdentityClientSecret`** |

## Doppler — `doppler`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## NetScaler — `netscaler`

| `method` | `credentials` fields |
|---|---|
| `basic-auth` | **`hostname`**, `port`, **`username`**, **`password`**, `sslRejectUnauthorized`, `sslCertificate` |

## Anthropic — `anthropic`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`** |

## OVH — `ovh`

| `method` | `credentials` fields |
|---|---|
| `certificate` | **`privateKey`**, **`certificate`**, **`okmsDomain`**, **`okmsId`** |

## Devin — `devin`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`** |

## Ona — `ona`

| `method` | `credentials` fields |
|---|---|
| `personal-access-token` | **`personalAccessToken`** |

## DigiCert — `digicert`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`**, **`region`** |

## Travis CI — `travis-ci`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`apiToken`** |

## Salesforce — `salesforce`

| `method` | `credentials` fields |
|---|---|
| `client-credentials` | **`instanceUrl`**, **`consumerKey`**, **`consumerSecret`** |

## Snowflake — `snowflake`

| `method` | `credentials` fields |
|---|---|
| `username-and-token` | **`account`**, **`username`**, **`password`** |

## Datadog — `datadog`

| `method` | `credentials` fields |
|---|---|
| `token` | **`url`**, **`apiKey`**, **`applicationKey`** |
| `api-key` | **`url`**, **`apiKey`**, **`applicationKey`** |

## F5 BIG-IP — `f5-big-ip`

| `method` | `credentials` fields |
|---|---|
| `basic-auth` | **`hostname`**, `port`, **`username`**, **`password`**, `sslRejectUnauthorized`, `sslCertificate` |

## GoDaddy — `godaddy`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`**, **`apiSecret`** |

## Convex — `convex`

| `method` | `credentials` fields |
|---|---|
| `personal-access-token` | **`accessToken`**, `instanceUrl` |

## Rundeck — `rundeck`

| `method` | `credentials` fields |
|---|---|
| `api-token` | **`instanceUrl`**, **`apiToken`** |

## Hasura Cloud — `hasura-cloud`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`** |

## Qovery — `qovery`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`** |

## Cloud 66 — `cloud-66`

| `method` | `credentials` fields |
|---|---|
| `access-token` | **`accessToken`** |

## LiteLLM — `litellm`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`apiKey`**, **`instanceUrl`** |

## Fireworks — `fireworks`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`accountId`**, **`apiKey`** |

## Kemp LoadMaster — `kemp-loadmaster`

| `method` | `credentials` fields |
|---|---|
| `basic-auth` | **`hostname`**, `port`, **`username`**, **`password`**, `sslRejectUnauthorized`, `sslCertificate` |

## Microsoft Intune — `microsoft-intune`

| `method` | `credentials` fields |
|---|---|
| `client-secret` | **`tenantId`**, **`clientId`**, **`clientSecret`** |

## Nutanix Prism Central — `nutanix-prism-central`

| `method` | `credentials` fields |
|---|---|
| `api-key` | **`hostname`**, `port`, `sslRejectUnauthorized`, `sslCertificate` |
| `basic-auth` | **`hostname`**, `port`, `sslRejectUnauthorized`, `sslCertificate` |

## Spacelift — `spacelift`

| `method` | `credentials` fields |
|---|---|
| `api-key-secret` | **`apiUrl`**, **`apiKeyId`**, **`apiKeySecret`** |

