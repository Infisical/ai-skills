# Platform Syncs: GitHub, Vercel, Cloudflare

## GitHub

### Prerequisites
- GitHub Connection (via GitHub App or OAuth)
- Network allows inbound requests from Infisical

### Destination Config
| Field | Required | Description |
|-------|----------|-------------|
| GitHub Connection | Yes | The App Connection to authenticate with |
| `scope` | Yes | Where secrets are deployed: `repository`, `organization`, or `repository-environment` |

Note the environment scope value is **`repository-environment`**, not `environment`.

**If `scope = "organization"`:**
| Field | Required | Description |
|-------|----------|-------------|
| Organization Name | Yes | GitHub org name |
| `visibility` | Yes | `all`, `private` (requires Pro/Team), or `selected` |
| Selected Repository IDs | If `visibility = "selected"` | Specific repos to grant access |

Visibility values are the short forms `all` / `private` / `selected` — not
`all-repositories` / `private-repositories` / `selected-repositories`.

**If `scope = "repository"`:**
| Field | Required | Description |
|-------|----------|-------------|
| Repository | Yes | Target repository (owner + repo) |

**If `scope = "repository-environment"`:**
| Field | Required | Description |
|-------|----------|-------------|
| Repository | Yes | Target repository |
| Environment | Yes | GitHub environment name (e.g., `production`, `staging`) |

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | **Only `overwrite-destination`** — GitHub does not support importing secrets |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |

### Gotchas
- **GitHub does not support importing secrets.** You cannot read existing GitHub secrets back — only overwrite. This means the initial sync will always be a one-way push.
- Org visibility options depend on GitHub plan (Pro/Team required for `private`)
- Environment secrets require the environment to already exist in the repository settings

---

## Vercel

### Prerequisites
- Vercel Connection
- Network allows inbound requests from Infisical

### Destination Config

Vercel syncs have a `scope` discriminator — `project` or `team`. The required fields differ.

**Common to both scopes:**
| Field | Required | Description |
|-------|----------|-------------|
| Vercel Connection | Yes | The App Connection to authenticate with |
| `scope` | Yes | `project` or `team` |
| `teamId` | Yes | Vercel team ID — required in **both** scopes |

**If `scope = "project"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `app` | Yes | Vercel app (project) ID |
| `appName` | Yes | Vercel app name |
| `env` | Yes | Target environment: `development`, `preview`, `production`, or a custom environment slug |
| `branch` | No | Specific branch for preview deployments |
| `sensitive` | No | Mark synced variables as Vercel sensitive env vars (default `false`) |

**If `scope = "team"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `teamName` | No | Vercel team name |
| `targetEnvironments` | No | Array of `development` / `preview` / `production` (default `[]`) |
| `applyToAllCustomEnvironments` | No | Apply to every custom environment (default `false`) |

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination`, `import-prioritize-source`, or `import-prioritize-destination` |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |

### Gotchas
- **`teamId` is required even for project scope.** Omitting it is the most common Vercel sync misconfiguration.
- **Vercel does not expose sensitive env var values.** During initial import, Vercel sensitive variables come in with empty values because Vercel's API doesn't return them.
- After first sync, users must manually re-enter any sensitive variable values in Infisical to keep both platforms aligned.
- Setting `sensitive = true` means Infisical can no longer read those values back from Vercel on a later import.
- Preview branch is optional — if set, secrets only apply to that branch's preview deployments
- `env` accepts custom Vercel environment slugs, not just the three built-ins

---

## Cloudflare Workers

### Prerequisites
- Cloudflare Connection

### Destination Config
| Field | Required | Description |
|-------|----------|-------------|
| Cloudflare Connection | Yes | The App Connection to authenticate with |
| `scriptId` | Yes | The Workers script to sync secrets to. Max 64 chars, lowercase alphanumerics and dashes, must start and end alphanumeric |

### Sync Options
| Field | Description |
|-------|-------------|
| Initial Sync Behavior | `overwrite-destination` only — no import support (`canImportSecrets: false`) |
| Key Schema | Template for key transformation |
| Auto-Sync Enabled | Default on |
| Disable Secret Deletion | Prevent deletion at destination |
| `syncNonSecretBindings` | Also manage the script's plain-text (non-secret) bindings |

### Gotchas
- Like GitHub, Cloudflare Workers does not support importing existing secrets
- Secrets are synced as Workers secrets (encrypted environment variables). Set `syncNonSecretBindings` if you also want Infisical to manage plain-text bindings
- `scriptId` must match Cloudflare's naming rules — `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`
