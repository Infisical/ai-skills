# Approval Workflows, Access Requests, and Audit

Approval workflows and access requests are **Enterprise tier** on Infisical Cloud, and require an
enterprise license when self-hosting.

## Two kinds of approval policy

Do not conflate these — they gate different things:

| Policy | Gates | Answers |
|--------|-------|---------|
| **Change approval** (secret approval) | Modifications to secrets | "Can this change land?" |
| **Access approval** | Granting access to an environment or path | "Can this person get in?" |

Change approval reviews a diff. Access approval reviews a person. A project frequently wants both:
review changes to prod secrets, *and* review who is allowed to read them at all.

## Change approval policies

Require that changes to secrets in a given environment and path be reviewed before they take effect.
The pending change is a **change request**, reviewed on **Project → Approvals**.

### Prerequisites

- **Create** permission on **Secret Approval** for the project. Typically project admins, or a custom role with explicit Secret Approval permissions.

### Configuration

A policy is scoped to an environment and a secret path, with a set of approvers and a number of
approvals required.

Approvers are **users or groups** (`ApproverType`: `user`, `group`). Prefer groups so the policy
survives staffing changes.

### Bypass approvals (break-glass)

A **Bypass Approvals** toggle allows nominated users to bypass the requirement in break-glass
situations. Three details that matter:

1. **If bypass is enabled but no users or groups are selected, *anyone* can bypass.** That is the trap — enabling the toggle without specifying bypassers effectively disables the policy. Always name the bypassers.
2. **A bypass can only be performed by the person who created the change request.** Bypassers cannot bypass requests submitted by others, so this is not a way to approve someone else's change.
3. **All approvers are notified by email when a bypass happens.** It is loud by design.

`BypasserType` is `user` or `group`, same as approvers.

Recommend enabling bypass with a small, named group — an on-call rotation — rather than leaving it
off entirely. A policy nobody can bypass during an incident gets disabled during the incident, which
is worse.

### Notifications

Approvers are notified by **email**, **Slack**, or **Microsoft Teams** when a change request is
submitted.

Wire up Slack or Teams. An approval workflow whose notifications go only to email gets ignored, and
then the workflow becomes a source of delay rather than safety.

## Access requests

Lets users request **temporary or permanent** access to secrets in specific environments and folders,
rather than having it granted up front.

Administrators define policies controlling:

- Who can approve requests
- Time limits
- Expiration rules

The pattern this enables, and the one worth recommending for production: **nobody holds standing
access**. Access is requested when needed, approved, and expires. Combined with temporary access (see
`references/roles-and-permissions.md`) this removes standing privilege without blocking work.

Contrast with PAM access requests (`infisical-pam`), which gate *sessions on infrastructure
accounts*. These gate *access to secrets*. Same idea, different products.

## Choosing what to gate

| Scenario | Control |
|----------|---------|
| Changes to prod secrets | Change approval policy |
| Who can read prod secrets at all | Access approval policy + no standing access |
| A one-off exception for one person | Additional privilege, temporary |
| Rolling back a bad change | `secret-rollback` permission with `perform-rollback` |
| Emergency during an incident | Named bypassers on the change policy |

Do not gate everything. Approval on dev and staging produces reflexive approving, which trains people
to click through the prod one too.

## Audit logs

Every action produces an audit record. The `audit-logs` subject exists at both org and project level,
so you can grant log access without granting anything else — a good fit for a security team or an
auditor role.

## Audit log streams

Streams push audit events to an external system as they happen.

### Providers

`LogProvider`:

| Provider | Value |
|----------|-------|
| Splunk | `splunk` |
| Datadog | `datadog` |
| Azure | `azure` |
| Cribl | `cribl` |
| Sumo Logic | `sumo-logic` |
| Custom webhook | `custom` |

`custom` posts to an endpoint you control, for anything not in the list.

### Stream mode

`StreamMode`:

| Value | Behavior |
|-------|----------|
| `batch` | A JSON **array** of events per request. **Default for all new streams** |
| `single` | One event per request — legacy custom-webhook behavior |

New streams default to `batch`. If a user is writing a custom webhook receiver, tell them to expect a
**JSON array**, not a single object. A receiver written against `single` semantics will mis-parse
batched deliveries, and this is the most likely integration bug.

### Product filtering

Streams can be scoped with `filters.products` using `AuditLogStreamProduct`:

| Value | Covers |
|-------|--------|
| `secret-manager` | Secrets Management projects |
| `cert-manager` | Certificate Management projects |
| `kms` | KMS projects |
| `secret-scanning` | Secret Scanning projects |
| `pam` | PAM projects |
| `organization` | **Org-level events with no associated project** — SSO, org settings, user and identity management |

An **absent or empty** `filters.products` list means **stream all products**.

The `organization` value is the one to point out: org-level events — SSO configuration changes, user
management, identity creation — belong to no project, so a stream filtered to only product values
will silently miss them. If a user wants complete coverage, either omit the filter entirely or
include `organization`.

The product values are kept 1:1 with `ProjectType`, so a project's `type` maps directly to a product
value.

### Credentials

Stream credentials are redacted when read back — the API returns `******` rather than the stored
value. Users cannot retrieve a stream's token after creating it; they must replace it.

## Recommendations

- **Stream to wherever the security team already looks.** Audit logs read only in the Infisical UI after an incident are not a detection control.
- **Include `organization` in product filters**, or omit the filter, so SSO and identity events are captured.
- **Expect batched arrays** in custom webhook receivers.
- **Alert on specific events**, not on volume: assume-privilege use, bypassed change requests, permission grants, failed authentication.
- **Grant `audit-logs` read to auditors** rather than a broader role.
