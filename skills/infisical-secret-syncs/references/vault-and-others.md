# HashiCorp Vault & Other Syncs

## HashiCorp Vault

### Prerequisites
- HashiCorp Vault Connection (token or AppRole auth)

API `destination` value: `hashicorp-vault`

### Destination Config
| Field | Required | Description |
|-------|----------|-------------|
| Vault Connection | Yes | The App Connection to authenticate with |
| `mount` | Yes | KV secrets engine mount point (e.g., `secret`, `kv`). Max 128 chars |
| `path` | Yes | Path within the engine (e.g., `dev/nested`, `myapp/config`). Max 128 chars |

`path` accepts alphanumerics, dots, dashes, underscores, and single slashes between segments.
Leading and trailing slashes are stripped automatically.

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |

### Gotchas
- Paths are auto-created if they don't exist — no need to pre-create them in Vault
- Works with KV v2 secrets engines
- Import is supported (`canImportSecrets: true`), so this is useful for migrating from Vault to Infisical gradually — sync back to Vault while transitioning
- The import enum values are `import-prioritize-source` (Infisical wins) and `import-prioritize-destination` (Vault wins). There is no `import-prioritize-hashicorp-vault`

---

## Other Supported Destinations

All destinations follow the same general pattern: App Connection → Source → Destination → Sync Options. Key differences are in the destination config fields.

### AWS Parameter Store
- **Destination Config:** `region`, `path`, `keyId` (KMS key, optional), `tags`, `syncSecretMetadataAsTags`
- **Mapping:** Each Infisical secret → separate SSM parameter
- **Type:** Secrets stored as `SecureString` parameters

### GitLab
- **Destination Config:** `scope` (`project` or `group`), then `projectId`/`projectName` or `groupId`/`groupName`, plus `targetEnvironment`, `shouldProtectSecrets`, `shouldMaskSecrets`, `shouldHideSecrets`
- **Mapping:** CI/CD variables

### Bitbucket
- **Destination Config:** `workspaceSlug`, `repositorySlug`, `environmentId` (optional — for deployment-environment variables)
- **Mapping:** Repository variables

### Netlify
- **Destination Config:** `accountId`, `accountName`, `siteId`, `siteName`, `context`

### Railway
- **Destination Config:** `projectId`, `projectName`, `environmentId`, `environmentName`, `serviceId`, `serviceName`

### Render
- **Destination Config:** `scope` (`service` or `environment-group`), then `serviceId` + `autoRedeployServices`, or `environmentGroupId`; plus `type`

### Fly.io
- **Destination Config:** `appId`, `autoRedeploy`

### Heroku
- **Destination Config:** `app`, `appName`
- **Note:** Secrets synced as config vars — Heroku restarts the dyno on changes

### Terraform Cloud
- **Destination Config:** `scope` (`variable-set` or `workspace`), `org`, then `variableSetId`/`variableSetName` or `workspaceId`/`workspaceName`, plus `category`
- **Mapping:** Workspace or variable-set variables

### Databricks
- **Destination Config:** `scope` (the Databricks secret scope). The workspace host comes from the App Connection

### 1Password
- **Destination Config:** `vaultId`, `valueLabel`

### Supabase
- **Destination Config:** `projectId`, `projectName`

### TeamCity
- **Destination Config:** `project`, `buildConfig` (optional)

### CircleCI
- **Destination Config:** `orgName`, `projectName`, `projectId`

### Digital Ocean App Platform
- **Destination Config:** `appId`, `appName`

### Snowflake
- **Destination Config:** `database`, `schema`

### Rundeck
- **Destination Config:** `project`, `path`

### Hasura Cloud
- **Destination Config:** `projectId`, `projectName`

### Qovery
- **Destination Config:** `organizationId`, `organizationName`, `projectId`, `projectName`, `environmentId`, `environmentName`, `variableType`

### Cloud 66
- **Destination Config:** `stackId`, `stackName`

### Spacelift
- **Destination Config:** `contextId`, `contextName`, `configType`, plus `mountPath` / `fileMountFormat` when mounting as a file, and `writeOnly`

### OVH
- **Destination Config:** `path`

### Travis CI
- **Destination Config:** `repositoryId`, `repositorySlug`, `branch`

### Trigger.dev
- **Destination Config:** `projectRef`, `environment`, `markAsSecret`

### Azure App Configuration
- **Destination Config:** `configurationUrl`, `label` (optional)

### Azure Entra ID SCIM
- **Destination Config:** `servicePrincipalId`, `servicePrincipalDisplayName`

### Devin
- **Destination Config:** `orgId`

### Ona
- **Destination Config:** `projectId`, `projectName`

### Infisical (external instance)
- **Destination Config:** `projectId`, `environment`, `secretPath` (on the target instance)
- **Use case:** replicating secrets between two Infisical instances (e.g. cloud → self-hosted)

Several destinations take both an ID and a display-name field (`projectId` + `projectName`,
`stackId` + `stackName`, and so on). The ID is what the sync resolves against; the name field is
for readability in the UI. Supply both.

For any sync not covered above, check the per-destination page under
`docs/integrations/secret-syncs/` or the API reference for the create-sync request body — each
destination has its own `destinationConfig` schema.

## Choosing a Sync Destination

| If the user wants to... | Recommend... |
|--------------------------|-------------|
| Secrets in AWS services | AWS Secrets Manager (app-level) or AWS Parameter Store (config/infra-level) |
| Secrets in GCP services | GCP Secret Manager |
| Secrets in Azure services | Azure Key Vault |
| Secrets in GitHub Actions | GitHub sync with `repository` or `environment` scope |
| Secrets in Vercel deployments | Vercel sync targeting the correct app + environment |
| Gradual migration from Vault | HashiCorp Vault sync (bidirectional via import) |
| Secrets in CI/CD pipelines | GitHub, GitLab, Bitbucket, CircleCI, or TeamCity sync depending on their CI provider |
| Secrets in PaaS platforms | Vercel, Netlify, Railway, Render, Fly.io, Heroku, or Digital Ocean sync |
