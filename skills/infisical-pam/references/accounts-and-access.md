# PAM Accounts, Folders, Templates, and Access

## The 13 account types

`PamAccountType` values:

### Databases

| Type | Value |
|------|-------|
| PostgreSQL | `postgres` |
| MySQL | `mysql` |
| Microsoft SQL Server | `mssql` |
| OracleDB | `oracledb` |
| MongoDB | `mongodb` |
| Redis | `redis` |

### Servers

| Type | Value |
|------|-------|
| SSH | `ssh` |
| Windows (local) | `windows` |
| Windows AD (domain) | `windows-ad` |

### Platforms and cloud

| Type | Value |
|------|-------|
| Kubernetes | `kubernetes` |
| AWS IAM | `aws-iam` |
| GCP service account | `gcp-service-account` |
| Azure CLI | `azure-cli` |

An account holds the connection details (host, port, database) and the credentials. Whoever
connects goes through Infisical and never sees them.

### Per-type auth options

**SSH** — `PamSshAuthMethod`:

| Value | Meaning |
|-------|---------|
| `password` | Password authentication |
| `public-key` | Key-based |
| `certificate` | Certificate-based |

**GCP service account** — `GcpServiceAccountAuthMethod`:

| Value | Meaning |
|-------|---------|
| `impersonation` | Impersonate the service account. Preferred — nothing static stored |
| `static-key` | A service account key file |

## Folders

Folders group accounts **by who needs access to them**. Permissions are set at the folder level and
cascade to every account inside.

Organize by team (`backend-team`), department (`engineering`), application
(`checkout-service`), or environment — whatever matches how access actually works.

The design rule: if the same people need the same accounts, one folder. If different people need
different accounts, separate folders. Do **not** organize by technology — a `postgres` folder forces
you to grant everyone who needs any Postgres access to all of it.

Folders can carry a chat notification config subscribing to `PamNotificationEvent`:

| Event | Meaning |
|-------|---------|
| `access-requested` | Someone requested access |
| `access-request-approved` | A request was approved |
| `access-request-denied` | A request was denied |

Route these to the channel where approvers actually are, or requests will sit unanswered.

## Account templates

A template defines the policy applied when someone connects:

- Maximum session duration
- Whether a **reason** is required
- Whether **MFA** is required

Templates are **type-specific** — an SSH template cannot be used by a Postgres account. Every
account uses a template of its own type. Infisical ships sensible defaults for each type, so you can
create accounts immediately.

Create custom templates when environments differ: a `prod-postgres` template requiring a reason and
MFA with a 1-hour cap, alongside a `dev-postgres` template with neither and a longer cap.

Type-specificity exists so future policies can be type-aware — command restrictions for SSH, query
restrictions for databases.

Recommendation: on any production template, require a reason and MFA. The reason is what makes the
audit trail useful six months later; without it you know someone connected but not why.

## Memberships

A membership assigns a **user, group, or machine identity** (`PamMemberKind`: `user`, `group`,
`identity`) a role on a folder or account.

| Role (`PamResourceRole`) | Capabilities |
|--------------------------|-------------|
| `admin` | Full control — accounts, folders, sessions, memberships |
| `connector` | Launch sessions and connect to accounts |
| `auditor` | View audit logs and session recordings |

Separately, `PamProductRole` (`admin`, `member`) governs product-level ability to create Accounts
and Folders.

Folder memberships cascade to all accounts inside. Prefer folder-level grants; use account-level
grants only for genuine exceptions, because per-account grants are the thing that drifts and becomes
impossible to audit.

Assign **groups**, not individual users, wherever your identity provider supports it — then access
follows the group and departures are handled by offboarding. See `infisical-sso` for SCIM group
provisioning.

## Access requests (just-in-time)

For accounts sensitive enough that *having* access should not be enough to *use* it.

Two layers apply to a gated account, and **both are required**:

| Layer | What it grants |
|-------|---------------|
| **Membership** | The right to ever launch a session — `connector` or `admin` on the folder or account |
| **Approval** | Clearance to use that right *right now*, for a requested duration |

The constraint people miss: **a member can only request access on an account where they already hold
use access.** If they cannot already launch a session, there is nothing to request. Access requests
are not a way to grant access to someone who has none — they are a checkpoint on access already
granted.

Flow: member requests access on an account they can already use → approver signs off → access opens
for the requested duration → duration expires → access closes again.

`PamAccessStatus` tracks the caller's just-in-time state:

| Value | Meaning |
|-------|---------|
| `none` | No request in play |
| `pending` | Requested, awaiting approval |
| `granted` | Approved, access currently open |

AI agents go through the same checkpoint. An agent requests as whoever started it — a person or a
machine identity — and waits for an approver either way.

Use gating on production databases and domain admin accounts. Leave dev accounts ungated; approval
fatigue makes approvers rubber-stamp everything, which is worse than no gate.

## Discovery

Discovery scans external systems for privileged accounts you may not know exist, stages them for
review, and lets you import chosen ones as managed accounts.

Available to **Product Admins** only.

Use it when onboarding onto PAM: find the accounts scattered across the estate before deciding what
to manage. The account that causes an incident is usually one nobody had inventoried.

Discovery stages findings for review rather than importing automatically — nothing comes under
management without a decision.

## Account dependencies

A **dependency** is a Windows service, scheduled task, or IIS application pool that runs *as* one of
your accounts and therefore holds a copy of that account's password.

**Windows accounts only** — `windows` (local) and `windows-ad` (domain).

Why it matters: rotating a Windows service account's password would break every service still
holding the old one. Infisical **detects** dependencies during discovery and **syncs** them during
rotation, so rotation does not take down the services depending on that account.

This is the answer when a user says they cannot rotate a Windows service account because too much
depends on it. Run discovery to enumerate the dependencies, then rotate — Infisical updates them.

## Account credential rotation

PAM accounts support credential rotation, so the stored credential does not go stale.

Distinguish this from `infisical-secret-rotation`:

| | PAM account rotation | Secret Rotation |
|---|---|---|
| What holds the credential | The PAM account, never exposed | An Infisical secret applications read |
| Who consumes it | Nobody directly — PAM proxies | Applications reading the secret |
| Windows dependency sync | Yes | No |

If the credential is only ever used through brokered sessions, rotate it in PAM. If applications
need to read it, that is Secret Rotation.

## Access methods

`PamAccessMethod`:

| Value | Meaning |
|-------|---------|
| `web` | Browser-based session |
| `cli` | Through the Infisical CLI |

Web needs nothing installed — good for occasional human access and for auditors. CLI suits engineers
who want their own tooling, and is what agentic access builds on. See
`references/sessions-and-agents.md`.
