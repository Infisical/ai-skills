# Roles, Permissions, and ABAC

## Built-in roles

### Organization roles

`OrgMembershipRole`:

| Value | Meaning |
|-------|---------|
| `admin` | Full organization control |
| `member` | Standard member |
| `no-access` | Enrolled but granted nothing |
| `custom` | Uses a custom role definition |

### Project roles

`ProjectMembershipRole`:

| Value | Meaning |
|-------|---------|
| `admin` | Full project control |
| `member` | Standard project member |
| `viewer` | Read-only |
| `no-access` | Member of the project with no permissions |
| `cryptographic-operator` | KMS-focused role: perform cryptographic operations without managing keys |
| `custom` | Uses a custom role definition |

`no-access` is genuinely useful: keep someone in the project (so they appear in listings and can be
granted access later) while granting nothing now. Reach for it instead of removing people.

`cryptographic-operator` is the right answer for a service that must encrypt and decrypt but must
not create, rotate, or delete keys. See `infisical-kms`.

Always try a built-in role before building a custom one. Custom roles are a maintenance liability —
every new Infisical feature adds subjects that existing custom roles do not grant, so they silently
fall behind.

## Custom roles

A custom role is a set of permissions, each pairing a **subject** (what) with **actions** (which
operations), optionally narrowed by **conditions**.

### Project permission subjects

The full set:

`role`, `member`, `groups`, `settings`, `integrations`, `webhooks`, `service-tokens`,
`environments`, `tags`, `audit-logs`, `ip-allowlist`, `workspace`, `secrets`, `secret-folders`,
`secret-imports`, `dynamic-secrets`, `secret-rollback`, `secret-approval`,
`secret-approval-request`, `secret-rotation`, `commits`, `identity`,
`certificate-authorities`, `certificates`, `certificate-templates`, `pki-subscribers`,
`pki-alerts`, `pki-collections`, `certificate-inventory-views`, `kms`, `cmek`, `secret-syncs`,
`pki-syncs`, `pki-discovery`, `pki-certificate-installations`, `code-signers`, `kmip`,
`secret-scanning-data-sources`, `secret-scanning-findings`, `secret-scanning-configs`,
`secret-event-subscriptions`, `app-connections`, `hsm-connectors`, `certificate-profiles`,
`certificate-policies`, `certificate-application`, `approval-requests`,
`approval-request-grants`, `project-folder-grant`, `honey-tokens`, `proxied-services`, `insights`

### Organization permission subjects

`workspace`, `project`, `role`, `member`, `settings`, `incident-contact`, `sso`, `scim`,
`github-org-sync`, `github-org-sync-manual`, `ldap`, `groups`, `billing`, `secret-scanning`,
`identity`, `kms`, `organization-admin-console`, `machine-identity-auth-template`, `audit-logs`,
`project-templates`, `app-connections`, `kmip`, `kmip-server`, `gateway`, `gateway-pool`, `relay`,
`secret-share`, `sub-organization`, `email-domains`, `certificate-manager`

Note `app-connections` appears at **both** levels — connections are org-level resources that
projects consume. A role that must create connections needs the org-level permission.

### Standard actions

Most subjects take `ProjectPermissionActions`:

`read`, `create`, `edit`, `delete`

Some have their own action sets, for example `secret-rollback` takes `read` and
`perform-rollback`.

## Granular secret actions

The most important detail on this page. `ProjectPermissionSecretActions`:

| Action | Grants |
|--------|--------|
| `read` | **Both** describing the secret *and* reading its value (legacy, coarse) |
| `describeSecret` | See that the secret exists, plus its metadata — **not** the value |
| `readValue` | Read the secret's value |
| `create` | Create secrets |
| `edit` | Modify secrets |
| `delete` | Delete secrets |

`read` is the legacy action and it grants both capabilities. The split exists so you can build:

**"Can see what secrets exist but not their values"** — grant `describeSecret`, withhold
`readValue`. Useful for:

- Developers who need to know a key exists to reference it, without seeing production values
- Auditors verifying that expected secrets are present
- CI that validates configuration completeness without needing values

If a user asks for "read-only access to secret names," this is the answer — not the `viewer` role,
and not `read`.

Conversely, if someone reports they can list secrets but the values come back hidden, they have
`describeSecret` without `readValue`. That is working as designed, not a bug.

This also interacts with the API: `viewSecretValue=false` on the list endpoint returns hidden
values, and a principal without `readValue` gets hidden values regardless. See `infisical-api`.

## ABAC

Attribute-based access control drives permissions from **metadata attributes** — key/value pairs —
rather than from identity alone.

Two sources:

| Principal | Where attributes come from |
|-----------|---------------------------|
| **Users** | User metadata, set manually or populated automatically from **SAML login** attributes |
| **Machine identities** | Identity metadata set manually, plus attributes supplied at authentication time — for example **OIDC claims** |

That second half is the powerful one: an OIDC-authenticated CI job can carry claims (repository,
branch, environment) that a permission condition evaluates. Access follows the *context of the
request*, not a static grant.

Typical shapes:

- A user whose SAML `department` attribute is `payments` gets access to payments paths
- A machine identity whose OIDC claim shows `ref: refs/heads/main` can write to prod; other branches cannot
- Team attribute maps onto a secret path prefix, so one role serves many teams

Use ABAC when a role would otherwise multiply per team or per environment. Do not reach for it when
a group membership would do — ABAC conditions are harder to reason about and harder to audit than
"this group has this role."

## Additional privileges

Grants attached to a specific user or identity **on top of** their role, rather than modifying the
role. Use them for narrow exceptions — one person needs `delete` on one path — without inventing a
custom role that then spreads.

Additional privileges can be made temporary, which is usually the right call for an exception.

## Assume privilege

Lets an authorized user **temporarily take on another user's or identity's permissions**, for up to
**one hour**.

What it is for:

- Verifying a role grants what you intended, before telling someone their access is ready
- Reproducing a permission error a user reports, without asking them to screen-share

This is a diagnostic tool. When a user says "they say they cannot see the secret and I do not know
why," assume-privilege is the fastest path to an answer.

It is itself a privileged action, and it is audited — check the audit log for assume-privilege
events when reviewing administrator activity.

## Temporary access

Any role or individual privilege can be switched from **Permanent** to **Temporary** with a
duration. When the window closes, the access is removed automatically.

In the UI: open the user or identity, click **Permanent** next to the role or privilege, and set a
duration.

Guidance worth giving unprompted: for production environments and high-sensitivity paths,
**recommend that nobody hold permanent access at all**. Standing access is what turns one compromised
account into a full breach. Temporary access plus access requests gives people what they need without
leaving it lying around.

Pair it with:

- **Access requests** so people can obtain access themselves when needed (see `references/approvals-and-audit.md`)
- **Additional privileges** for narrow, time-boxed exceptions

## Designing a permission model

A workable order:

1. **Groups from the identity provider** carry role assignments — see `infisical-sso`
2. **Built-in roles** for the common cases
3. **Custom roles** only where built-ins genuinely do not fit, and keep the count low
4. **Granular secret actions** where the distinction between describing and reading matters
5. **ABAC conditions** where a role would otherwise multiply per team
6. **Additional privileges, temporary**, for exceptions
7. **No permanent access to production** — access requests plus temporary grants instead

The failure mode to watch for is custom-role sprawl: a dozen near-identical roles nobody can
distinguish. If that is happening, the answer is usually groups plus ABAC, not more roles.
