Yes, both are supported.

## AWS ElastiCache

Provider type `aws-elasticache`. It provisions ElastiCache **users** through the AWS API, not via Redis `ACL SETUSER` commands, so it's a distinct provider from plain Redis.

**Prerequisites:**
- An AWS IAM principal with permissions to manage ElastiCache users and user groups
- The ElastiCache cluster must have RBAC/user-group support enabled

**Configuration:**
| Field | Required |
|---|---|
| `clusterName` | Yes |
| `region` | Yes |
| `auth.type` | Yes |
| `auth.accessKeyId` / `auth.secretAccessKey` | Depends on auth type |
| `creationStatement` | Yes |
| `revocationStatement` | Yes |

Unlike plain Redis, there's no implicit default flow here, both `creationStatement` and `revocationStatement` are required.

## Tailscale

Provider type `tailscale`. It has two independent discriminators: how Infisical authenticates (`auth.method`) and what kind of key it mints (`authType`).

**Authentication:**
| Method | Fields |
|---|---|
| `api_key` | `apiKey` |
| `oauth` | `clientId`, `clientSecret` |

**Key type (`authType`):** `auth_keys`, `oauth_keys`, or `federated_keys`

**Common fields:** `tailnet` (default `-`, meaning the token owner's default tailnet), `description` (max 50 chars), `tags` (default `[]`)

**If `authType = "auth_keys"`:** `reusable` and `preauthorized` (both default `false`)

**If `authType = "oauth_keys"` or `"federated_keys"`:** `scopes` (at least one required)

**Restrictions to know about:**
- `tags` is required when authenticating via OAuth token, and also required if scopes include `devices:core` or `auth_keys`
- Privilege-escalation scopes are blocked entirely, at both the schema and provider level: `auth_keys`, `oauth_keys`, `federated_keys`, `api_access_tokens`, and `all` can't be requested. A lease can't mint credentials capable of creating more credentials
- Use `-` for `tailnet` unless you're managing a tailnet other than the token owner's default
