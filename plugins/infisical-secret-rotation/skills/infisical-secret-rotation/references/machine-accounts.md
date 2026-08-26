# Rotation: LDAP and OS Local Accounts

**Every provider on this page is SINGLE-PHASE.** The old credential is invalidated the moment
rotation runs. There is no overlap and no grace period. Clients holding the previous password fail
to authenticate until they re-read the secret.

For all four: recommend `isAutoRotationEnabled: false` and manual rotation inside a maintenance
window, unless the consumer re-reads the secret on every use.

## LDAP Password — `ldap-password`

App Connection: `ldap`

| `parameters` | Required | Description |
|--------------|----------|-------------|
| `dn` | Yes | Distinguished Name of the entry whose password is rotated |
| `rotationMethod` | No | `connection-principal` or `target-principal` |
| `passwordRequirements` | No | Shape of the generated password |

| `secretsMapping` | Receives |
|------------------|----------|
| `dn` | The entry's DN |
| `password` | The rotated password |

### rotationMethod

| Value | Meaning |
|-------|---------|
| `connection-principal` | Infisical binds as the App Connection's own principal and changes the target entry's password. Requires that principal to hold password-reset rights over the target |
| `target-principal` | Infisical binds **as the target entry itself** and changes its own password |

Pick `connection-principal` when you have an admin bind account — it is the usual choice.
`target-principal` suits directories where entries may change their own password but no admin
account is available to you.

## Unix/Linux Local Account — `unix-linux-local-account`

App Connection: `ssh`

| `parameters` | Required | Description |
|--------------|----------|-------------|
| `username` | Yes | Local account whose password is rotated |
| `rotationMethod` | No | `login-as-target` or `login-as-root` |
| `useSudo` | No | Whether to use `sudo` when changing the password. **Defaults to `true`** |
| `passwordRequirements` | No | Shape of the generated password |

| `secretsMapping` | `username`, `password` |

### rotationMethod

| Value | How it works | Needs |
|-------|--------------|-------|
| `login-as-root` | SSH in as a privileged account from the App Connection and change the target user's password | A privileged SSH account; `useSudo` usually `true` |
| `login-as-target` | SSH in **as the target user** and change its own password | The target's **current password**, supplied once at setup |

### The `login-as-target` bootstrap requirement

With `login-as-target`, creation **fails validation** unless you also supply the account's current
password in `temporaryParameters`:

```json
{
  "parameters": {
    "username": "appuser",
    "rotationMethod": "login-as-target"
  },
  "temporaryParameters": {
    "password": "<the account's current password>"
  }
}
```

The error if you omit it: `Current password is required for initial rotation setup in login as
target method`.

`temporaryParameters` is used only to bootstrap the first rotation — Infisical needs to
authenticate as the target once before it owns the credential. It is not stored as part of the
rotation config. `login-as-root` does not need it.

## Windows Local Account — `windows-local-account`

App Connection: `smb`

| `parameters` | Required | Description |
|--------------|----------|-------------|
| `username` | Yes | Local Windows account to rotate |
| `rotationMethod` | No | `login-as-target` or `login-as-root` |
| `passwordRequirements` | No | Shape of the generated password |

| `secretsMapping` | `username`, `password` |

Same two rotation methods as Unix/Linux, and `login-as-target` carries the same
`temporaryParameters.password` bootstrap requirement. There is no `useSudo` — privilege comes from
the account used to connect.

## HP iLO Local Account — `hp-ilo-local-account`

App Connection: `ssh`

| `parameters` | Required | Description |
|--------------|----------|-------------|
| `username` | Yes | iLO local account to rotate |
| `rotationMethod` | No | `login-as-target` or `login-as-root` |
| `passwordRequirements` | No | Shape of the generated password |

| `secretsMapping` | `username`, `password` |

For HP Integrated Lights-Out management controllers. Same method options and the same
`login-as-target` bootstrap requirement.

## passwordRequirements

Shared across all four providers:

```json
"passwordRequirements": {
  "length": 24,
  "required": { "digits": 2, "lowercase": 2, "uppercase": 2, "symbols": 1 },
  "allowedSymbols": "!@#$%^&*"
}
```

- `length` — 1 to 250
- `required.*` — minimum count per character class, non-negative
- `allowedSymbols` — optional allowlist of symbols

Constrain `allowedSymbols` for OS accounts. Shell scripts, `smbclient` invocations, and connection
strings all mangle certain characters, and a password containing a backtick or a quote will produce
failures that look like rotation bugs but are quoting bugs.

## Operational guidance

Because these are all single-phase:

1. **Default to `isAutoRotationEnabled: false`.** Rotate deliberately.
2. **Know every consumer before rotating.** A single-phase rotation breaks anything holding the old value, immediately.
3. **Have the consumer re-read on failure.** The most robust pattern is an app that re-fetches the secret on an auth error and retries once.
4. **Rotate in a window** and watch authentication logs afterward.
5. If you need zero-downtime credentials for a Linux host, consider whether an **SSH dynamic secret** fits better — it issues short-lived CA-signed certificates instead of rotating a password, and needs no coordination with consumers. See `infisical-dynamic-secrets`.

That last point is worth raising proactively. Users often reach for local-account rotation when
what they actually want is ephemeral SSH access, which is a better fit and avoids single-phase
downtime entirely.
