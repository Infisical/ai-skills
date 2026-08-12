# Dynamic Secrets: SSH, Kubernetes, LDAP & SaaS Providers

Covers `ssh`, `kubernetes`, `ldap`, `github`, `tailscale`, `ibm-api-connect`, and `totp`.

## SSH Certificates

### Overview
Infisical generates an internal CA key pair and issues signed SSH certificates on demand. Target hosts trust the CA, and certificates expire automatically — no manual key rotation or revocation needed.

### How It Works
1. When you create the dynamic secret, Infisical generates a CA key pair
2. You configure target SSH servers to trust this CA
3. For each lease, Infisical generates an ephemeral key pair, signs it with the CA, and returns the private key + signed certificate
4. The certificate automatically expires when the lease TTL is up

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| Secret Name | Yes | Name for this dynamic secret |
| Default TTL | Yes | Default certificate validity (e.g., `1h`, `8h`) |
| Max TTL | Yes | Maximum certificate validity |
| Allowed Principals | Yes | Usernames the cert can authenticate as (e.g., `ubuntu`, `deploy`, `root`) |
| Key Algorithm | Yes | `ED25519` (default, recommended), `RSA 2048`, `RSA 4096`, `ECDSA P-256`, or `ECDSA P-384` |

### Target Host Setup

After creating the dynamic secret, you get a setup modal with two options:

**Automated (recommended):**
```bash
curl -H "Authorization: Bearer <token>" \
  "https://<infisical-url>/api/v1/dynamic-secrets/ssh-ca-setup/<id>" | sudo bash
```
This writes the CA to `/etc/ssh/infisical_ca.pub`, adds `TrustedUserCAKeys` to sshd_config, and restarts SSH.

**Manual:**
1. Save the CA public key to `/etc/ssh/infisical_ca.pub`
2. Add to `/etc/ssh/sshd_config`:
   ```
   TrustedUserCAKeys /etc/ssh/infisical_ca.pub
   ```
3. Restart SSH: `sudo systemctl restart sshd`

### Lease Generation
- Specify TTL (within Max TTL)
- **Specify principals — this is required.** Every SSH lease must pass at least one principal in
  `config.principals`, and each must appear in the dynamic secret's Allowed Principals list.
  Omitting them fails with "SSH lease requires at least one principal in config.principals";
  requesting one outside the list fails with "Requested principals not in allowed list".

### Lease Returns
| Field | Description |
|-------|-------------|
| `PRIVATE_KEY` | The ephemeral private key (downloadable as `key.pem`) |
| `SIGNED_KEY` | The CA-signed certificate (downloadable as `cert.pub`) |

In an Infisical Agent template these are `{{ .PRIVATE_KEY }}` and `{{ .SIGNED_KEY }}`, and the
`dynamicSecret` function needs its 6th `principals` argument:

```go
{{ with dynamicSecret "my-project" "dev" "/" "my-ssh-secret" "1h" "root,deploy" }}
{{ .PRIVATE_KEY }}
{{ .SIGNED_KEY }}
{{- end }}
```

### Usage
```bash
chmod 600 key.pem
ssh -i key.pem -o CertificateFile=cert.pub <principal>@<hostname>
```

### Gotchas
- **Certificates CANNOT be renewed.** The TTL is baked in at signing time. Create a new lease for a fresh certificate.
- Certificates remain valid until TTL even if the lease is revoked in Infisical
- Use short TTLs for security-sensitive environments

---

## Kubernetes Service Account Tokens

### Overview
Generate short-lived Kubernetes service account tokens on demand. Supports two credential types and two authentication methods.

### Credential Types

**Static** — Use an existing service account with predefined permissions. Infisical generates a token for it.

**Dynamic** — Infisical creates a temporary service account, binds it to a specified role, generates a token, and cleans up when the lease expires.

### Authentication Methods

**Token (API)** — Provide a cluster URL and a service account token with RBAC permissions to create tokens.

**Gateway** — Use an Infisical Gateway deployed in the cluster (for private clusters).

### Static Credentials + Token Auth

**RBAC Setup (apply to cluster):**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infisical-token-requester
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: tokenrequest
rules:
  - apiGroups: [""]
    resources: ["serviceaccounts/token", "serviceaccounts"]
    verbs: ["create", "get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tokenrequest
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: tokenrequest
subjects:
  - kind: ServiceAccount
    name: infisical-token-requester
    namespace: default
```

**Get the token:**
```bash
kubectl get secret infisical-token-requester-token -n default \
  -o=jsonpath='{.data.token}' | base64 --decode
```

**Config:**
| Field | Required | Description |
|-------|----------|-------------|
| Cluster URL | Yes | e.g., `https://kubernetes.default.svc` |
| Cluster Token | Yes | Token from RBAC setup above |
| Service Account Name | Yes | Existing SA to generate tokens for |
| Namespace | Yes | SA's namespace |
| Audiences | No | Token audiences |

### Dynamic Credentials + Token Auth

Requires expanded RBAC (create/delete service accounts + role bindings):

```yaml
rules:
  - apiGroups: [""]
    resources: ["serviceaccounts/token", "serviceaccounts"]
    verbs: ["create", "get", "delete"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["rolebindings", "clusterrolebindings"]
    verbs: ["create", "delete"]
```

**Important:** The token requester SA can only create bindings for roles it has access to itself.

**Config:**
| Field | Required | Description |
|-------|----------|-------------|
| Cluster URL | Yes | Kubernetes API server URL |
| Cluster Token | Yes | Token with expanded RBAC |
| Allowed Namespaces | Yes | Comma-separated (e.g., `default,kube-system`) |
| Role Type | Yes | `ClusterRole` or `Role` |
| Role | Yes | Name of the role to bind |
| Audiences | No | Token audiences |

### Lease Returns
- Kubernetes service account token (JWT)

### Gotchas
- **Tokens CANNOT be revoked.** Like GCP, K8s tokens are JWTs with baked-in expiration. Revoking the lease removes the Infisical record but the token stays valid until expiry.
- **Tokens CANNOT be renewed.** The lifetime is fixed at creation. Create a new lease for a new token.
- Use short TTLs (15m–1h) for security
- Dynamic credentials create temporary service accounts that are automatically cleaned up on lease expiry
- Gateway auth eliminates the need to expose the cluster API server publicly

---

## LDAP

Provider type: `ldap`

Supports two credential types, and the required fields differ.

**Common:**
| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | LDAP server URL |
| `binddn` | Yes | Bind DN Infisical authenticates as |
| `bindpass` | Yes | Bind password |
| `ca` | No | CA certificate |
| `sslRejectUnauthorized` | No | Verify TLS (default `true`) |
| `credentialType` | Yes | `dynamic` (default) or `static` |

**If `credentialType = "dynamic"`** — Infisical creates and deletes an LDAP entry per lease:
| Field | Required | Description |
|-------|----------|-------------|
| `creationLdif` | Yes | LDIF applied to create the entry |
| `revocationLdif` | Yes | LDIF applied to remove the entry |
| `rollbackLdif` | No | LDIF applied if creation partially fails |

**If `credentialType = "static"`** — Infisical rotates the password of an existing entry:
| Field | Required | Description |
|-------|----------|-------------|
| `rotationLdif` | Yes | LDIF applied to rotate the credential |

### Gotchas
- Supply `rollbackLdif` for dynamic credentials — without it, a half-created entry can be left behind
- Static mode does not create users; it rotates an existing one, so the lease returns credentials for a fixed DN

---

## GitHub App Tokens

Provider type: `github`

Issues short-lived GitHub App installation access tokens.

| Field | Required | Description |
|-------|----------|-------------|
| `appId` | Yes | Numeric GitHub App ID |
| `installationId` | Yes | Numeric GitHub App installation ID |
| `privateKey` | Yes | The GitHub App's private key (PEM) |

### Gotchas
- `appId` and `installationId` are **numbers**, not strings or slugs
- GitHub installation tokens expire on GitHub's own schedule (max 1 hour) and cannot be renewed — request a new lease
- The token's permissions are whatever the App installation grants; scope the App narrowly

---

## Tailscale

Provider type: `tailscale`

Issues Tailscale keys. Two independent discriminators: how Infisical authenticates
(`auth.method`) and what kind of key it mints (`authType`).

**Authentication (`auth.method`):**
| Method | Fields |
|--------|--------|
| `api_key` | `apiKey` — Tailscale API access token |
| `oauth` | `clientId`, `clientSecret` |

**Key type (`authType`):** `auth_keys`, `oauth_keys`, or `federated_keys`

**Common fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `tailnet` | No | Tailnet identifier; `-` (default) means the token owner's default tailnet |
| `description` | No | Applied to the created key (max 50 chars) |
| `tags` | No | ACL tags such as `tag:ci` (default `[]`) |

**If `authType = "auth_keys"`:**
| Field | Description |
|-------|-------------|
| `reusable` | Whether the key can register multiple devices (default `false`) |
| `preauthorized` | Whether registered devices are pre-authorized (default `false`) |

**If `authType = "oauth_keys"` or `"federated_keys"`:**
| Field | Description |
|-------|-------------|
| `scopes` | OAuth scopes granted to the created client (at least one required) |

### Gotchas
- **`tags` is required when authenticating with an OAuth token**, and also when scopes include `devices:core` or `auth_keys`
- **Privilege-escalation scopes are blocked** at both schema and provider level: `auth_keys`, `oauth_keys`, `federated_keys`, `api_access_tokens`, and `all`. A lease cannot mint credentials able to create more credentials
- Use `-` for `tailnet` unless you are managing a tailnet other than the token owner's default

---

## IBM API Connect

Provider type: `ibm-api-connect`

| Field | Required | Description |
|-------|----------|-------------|
| `clientId` | Yes | Client ID |
| `clientSecret` | Yes | Client secret |
| `instanceUrl` | Yes | API Connect instance URL |
| `apiKey` | Yes | API key |
| `orgId` | Yes | Organization |
| `catalogId` | Yes | Catalog |
| `consumerOrgId` | Yes | Consumer organization |
| `appId` | Yes | Application |
| `gatewayId` | No | Gateway |
| `gatewayPoolId` | No | Gateway pool |

---

## TOTP

Provider type: `totp`

Generates time-based one-time passwords rather than credentials. Useful for automating logins
that require an OTP. Two config types:

**If `configType = "url"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | An `otpauth://` URL. Must include a `secret` parameter |

**If `configType = "manual"`:**
| Field | Required | Description |
|-------|----------|-------------|
| `secret` | Yes | The TOTP shared secret (whitespace is stripped) |
| `period` | No | Step in seconds (default 30) |
| `algorithm` | No | Hash algorithm |
| `digits` | No | Code length (default 6) |

### Gotchas
- TOTP leases return a **code**, not a credential pair — the underlying secret is stored once and reused
- Unlike other providers, generating a lease does not create anything on a remote system
