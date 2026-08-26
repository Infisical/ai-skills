# App Connections: AWS, GCP, Azure

## AWS — `aws`

Two methods. **Prefer `assume-role`.**

### `assume-role` (recommended)

Infisical assumes an IAM role in your account. Nothing static is stored.

```json
{
  "name": "prod-aws",
  "method": "assume-role",
  "credentials": {
    "roleArn": "arn:aws:iam::123456789012:role/InfisicalAccess"
  }
}
```

| Credential field | Required | Notes |
|------------------|----------|-------|
| `roleArn` | Yes | The role Infisical assumes |
| `stsEndpoint` | No | Custom STS endpoint |

`stsEndpoint` is validated hard: it must be HTTPS **and** resolve to an AWS-owned domain
(`.amazonaws.com`, `.amazonaws.com.cn`). Custom or third-party hosts are rejected. Use it for
GovCloud, China regions, or a VPC PrivateLink STS endpoint — not for a proxy.

**Trust policy** — the role must trust Infisical's principal and require the External ID shown in
the Infisical UI when you set up the connection. Always tell the user to include the External ID
condition; a trust policy without it is confused-deputy vulnerable.

### `access-key` (fallback)

```json
{
  "method": "access-key",
  "credentials": {
    "accessKeyId": "AKIA...",
    "secretAccessKey": "..."
  }
}
```

Use only where role assumption is impossible. These are long-lived credentials you now have to
rotate — note that an `aws-iam-user-secret` Secret Rotation can rotate the very IAM user whose
keys you paste here, which is a reasonable mitigation.

### Permissions

Grant only what the consuming feature needs:

| Consumer | Needs |
|----------|-------|
| AWS Secrets Manager sync | `secretsmanager:` create/update/delete/list/describe, plus KMS if using a CMK |
| AWS Parameter Store sync | `ssm:PutParameter`, `GetParameter(s)`, `DeleteParameter`, `DescribeParameters`, plus KMS for `SecureString` |
| AWS IAM user secret rotation | `iam:CreateAccessKey`, `iam:DeleteAccessKey`, `iam:ListAccessKeys` on the target user |
| ElastiCache / MemoryDB dynamic secrets | The relevant `elasticache:` / `memorydb:` user-management actions |

## GCP — `gcp`

Exactly one method: `service-account-impersonation`. There is no service-account-key-file option,
so do not offer one.

```json
{
  "name": "prod-gcp",
  "method": "service-account-impersonation",
  "credentials": {
    "serviceAccountEmail": "infisical@my-project.iam.gserviceaccount.com"
  }
}
```

| Credential field | Required |
|------------------|----------|
| `serviceAccountEmail` | Yes — must be a valid email |

Setup on the GCP side:

1. Create a service account in your project
2. Grant Infisical's service account the **Service Account Token Creator** role on it, so Infisical can impersonate it
3. Grant the impersonated service account the permissions the feature needs

For the GCP Secret Manager sync, enable these APIs first, or connection creation and syncing fail
in confusing ways:

- Cloud Resource Manager API
- Secret Manager API
- Service Usage API

## Azure

Azure is split into **six** separate connection types. Choosing the wrong one is the most common
Azure mistake, because the names are similar and the credentials look identical.

| Connection | Slug | Use it for |
|------------|------|-----------|
| Azure Key Vault | `azure-key-vault` | Syncing secrets to a Key Vault |
| Azure App Configuration | `azure-app-configuration` | Syncing to App Configuration |
| Azure Client Secrets | `azure-client-secrets` | Rotating an app registration's client secret |
| Azure DevOps | `azure-devops` | Syncing to Azure DevOps variable groups |
| Azure Entra ID | `azure-entra-id` | Entra ID SCIM sync, Entra ID dynamic secrets |
| Azure DNS | `azure-dns` | ACME DNS-01 validation for PKI |

Plus two ADCS connections for certificate services, covered in `references/databases-and-infra.md`.

### Methods

| Connection | Methods |
|------------|---------|
| `azure-key-vault` | `oauth`, `client-secret`, `certificate` |
| `azure-client-secrets` | `oauth`, `client-secret`, `certificate` |
| `azure-app-configuration` | `oauth`, `client-secret` |
| `azure-entra-id` | `client-secret` |
| `azure-dns` | `client-secret` |

### `oauth`

A browser flow started from the Infisical UI. The create-time credential is the OAuth `code`:

```json
{
  "method": "oauth",
  "credentials": {
    "code": "<code from the OAuth redirect>",
    "tenantId": "<optional tenant id>"
  }
}
```

Infisical exchanges it for an access token and refresh token, which it then maintains. Because it
depends on an interactive redirect, `oauth` is awkward to script — prefer `client-secret` for
automation.

### `client-secret`

An Azure app registration's client credentials:

```json
{
  "method": "client-secret",
  "credentials": {
    "clientId": "<app registration client id — must be a UUID>",
    "clientSecret": "<client secret>",
    "tenantId": "<directory tenant id>"
  }
}
```

`clientId` is validated as a UUID and capped at 50 characters. Pass the **Application (client) ID**,
not the display name or the object ID.

### `certificate`

Certificate-based authentication for the app registration, available on `azure-key-vault` and
`azure-client-secrets`. Preferable to a client secret in regulated environments because there is no
shared secret to leak or expire silently.

### Azure Key Vault permissions

The app registration or user needs these secret permissions on the vault:

`secrets/list`, `secrets/get`, `secrets/set`, `secrets/recover`

The built-in **Key Vault Secrets Officer** role covers them. `secrets/recover` is required because
Azure soft-deletes secrets — without it, Infisical cannot re-create a secret that was deleted and
is still in the soft-delete window, and syncs fail on a name that "already exists" while being
invisible.

Remember Azure Key Vault converts underscores in secret names to hyphens. That belongs to the sync
configuration rather than the connection — see `infisical-secret-syncs`.

### Connection credential rotation

`azure-key-vault`, `azure-client-secrets`, `azure-app-configuration`, and `azure-entra-id` all
support rotating their **own** stored credential:

```json
{
  "method": "client-secret",
  "credentials": { "...": "..." },
  "isAutoRotationEnabled": true,
  "rotation": {
    "rotationInterval": 30,
    "rotateAtUtc": { "hours": 2, "minutes": 0 }
  }
}
```

This keeps the app registration's client secret from expiring — a real operational win, since
Azure client secrets have a hard expiry and a silently expired one breaks every sync using it.
It writes nothing into your project secrets.

## Choosing between them

| The user says... | Connection |
|------------------|-----------|
| "sync secrets to AWS Secrets Manager" | `aws` with `assume-role` |
| "sync to SSM Parameter Store" | `aws` with `assume-role` |
| "sync secrets to GCP" | `gcp` |
| "sync secrets into a Key Vault" | `azure-key-vault` |
| "rotate our Azure app's client secret into a secret" | `azure-client-secrets` |
| "keep Infisical's own Azure credential from expiring" | any Azure connection with `isAutoRotationEnabled` |
| "provision users into Entra ID" | `azure-entra-id` |
| "ACME certificates validated over Azure DNS" | `azure-dns` |
