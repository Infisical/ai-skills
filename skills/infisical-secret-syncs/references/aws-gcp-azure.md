# Cloud Secret Manager Syncs: AWS, GCP, Azure

## AWS Secrets Manager

### Prerequisites
- AWS Connection with **Secret Sync** permissions
- Network allows inbound requests from Infisical

API `destination` value: `aws-secrets-manager`

### Destination Config
| Field | Required | Description |
|-------|----------|-------------|
| AWS Connection | Yes | The App Connection to authenticate with |
| `region` | Yes | AWS region (e.g., `us-east-1`) |
| `mappingBehavior` | Yes | `one-to-one` (each secret → separate AWS secret) or `many-to-one` (all secrets → single AWS secret as JSON) |
| `secretName` | If `many-to-one` | Name of the single AWS secret to pack everything into |

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` (`canImportSecrets: true`) |
| Key Schema | Template for key transformation (e.g., `INFISICAL_{{secretKey}}`) |
| `keyId` | Optional AWS KMS key ID or alias for encryption |
| `tags` | Optional `{ key, value }` tags added to synced secrets |
| `syncSecretMetadataAsTags` | If enabled, Infisical metadata becomes AWS tags (manual tags take precedence) |
| Auto-Sync Enabled | Default on — sync on changes |
| Disable Secret Deletion | Prevent Infisical from deleting destination secrets |

### Gotchas
- **Mapping behavior is unique to AWS Secrets Manager.** No other destination has it — do not offer `one-to-one`/`many-to-one` for GCP, Azure, or anything else.
- Many-to-one is ideal for apps that read a single JSON secret; one-to-one is better for per-secret access patterns
- `secretName` is only meaningful with `many-to-one`

---

## GCP Secret Manager

### Prerequisites
- GCP Connection with **Secret Sync** permissions
- Enable APIs: Cloud Resource Manager API, Secret Manager API, Service Usage API
- Network allows inbound requests from Infisical

API `destination` value: `gcp-secret-manager`

### Destination Config

`scope` is a discriminator — the other fields depend on it.

**Common:**
| Field | Required | Description |
|-------|----------|-------------|
| GCP Connection | Yes | The App Connection to authenticate with |
| `scope` | Yes | `global` or `region` |
| `projectId` | Yes | GCP project ID |

**If `scope = "global"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `locationId` | No | Optional primary location |
| `userReplicaLocationIds` | No | Array of locations to replicate to (default `[]`) |

**If `scope = "region"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `locationId` | Yes | The GCP Secret Manager location for regional secrets |

`locationId` values are GCP Secret Manager location slugs (e.g. `us-central1`, `europe-west1`,
`asia-southeast1`), validated against a fixed list.

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` (`canImportSecrets: true`) |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |

### Gotchas
- Three GCP APIs must be enabled before creating the connection
- Regional scope restricts secret availability to that region only
- Global scope with `userReplicaLocationIds` is how you pin replication to specific locations while staying global

---

## Azure Key Vault

### Prerequisites
- Azure Key Vault Connection
- User/service principal needs these secret permissions: `secrets/list`, `secrets/get`, `secrets/set`, `secrets/recover`
- Recommended role: **Key Vault Secrets Officer**
- Network allows inbound requests from Infisical

API `destination` value: `azure-key-vault`

### Destination Config
| Field | Required | Description |
|-------|----------|-------------|
| Azure Connection | Yes | The App Connection to authenticate with |
| `vaultBaseUrl` | Yes | Full URL of the Key Vault (e.g., `https://my-vault.vault.azure.net`) |

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` (`canImportSecrets: true`) |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |
| `disableCertificateImport` | Skip importing certificate objects from Azure Key Vault |

### Gotchas
- **Underscores are converted to hyphens.** Azure Key Vault does not allow underscores in secret names. `DATABASE_URL` becomes `DATABASE-URL` at the destination.
- The `secrets/recover` permission is needed because Azure soft-deletes secrets — Infisical may need to recover a previously deleted secret before updating it.
