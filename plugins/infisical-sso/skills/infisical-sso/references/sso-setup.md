# SSO Setup

## Prerequisite: email domain verification

**Every** login integration on this page — SAML, OIDC, LDAP — requires
**Email Domain Verification** first. Verify the organization's email domain before configuring
anything else.

The verified domain is what makes the IdP authoritative for those addresses, which is why
enforcement and the password-signup block are tied to it.

## Choosing a protocol

| Protocol | Cost | Use when |
|----------|------|----------|
| **Google SSO** | Free | Google Workspace org, small team, want the simplest thing |
| **GitHub SSO** | Free | Team already organized around GitHub |
| **SAML 2.0** | Paid (Pro) | Enterprise IdP; SAML is the established standard there |
| **OIDC** | Paid (Pro) | Modern IdP, or you want group claims in tokens |
| **LDAP** | Paid (Enterprise) | On-premises directory is authoritative and there is no SAML/OIDC front end |

Prefer **OIDC over SAML** for new setups where the IdP supports both. Group membership arrives in a
`groups` claim on every login, which makes group mapping cleaner than SAML attribute plumbing.

Prefer **SAML** when the organization already standardizes on it or the IdP's OIDC support is
limited.

## Supported providers

### SAML 2.0

| Provider | Doc |
|----------|-----|
| Okta | `sso/okta` |
| Azure / Entra ID | `sso/azure` |
| JumpCloud | `sso/jumpcloud` |
| Google | `sso/google-saml` |
| Auth0 | `sso/auth0-saml` |
| Keycloak | `sso/keycloak-saml` |

### OIDC

| Provider | Doc |
|----------|-----|
| Okta | `sso/okta-oidc` |
| Auth0 | `sso/auth0-oidc` |
| PingOne | `sso/pingone-oidc` |
| Keycloak | `sso/keycloak-oidc/` |
| General / any OIDC provider | `sso/general-oidc/` |

The **General OIDC** path covers any compliant provider not listed. If a user's IdP is not named
above, that is the route — do not tell them it is unsupported.

### Free OAuth providers

Google SSO (`sso/google`), GitHub SSO (`sso/github`), GitLab SSO (`sso/gitlab`).

### LDAP

Paid, Enterprise tier. Provider guides for **Google Workspace**, **JumpCloud**, and a **general**
LDAP setup.

## PKCE

Infisical enforces **PKCE** (Proof Key for Code Exchange) on the OAuth 2.0-based SSO providers and on
OIDC. This protects against authorization-code interception.

It is on by default and not configurable — mention it if a user asks about the security of the flow,
but there is nothing to set up.

## SSO enforcement

Enforcing SAML or OIDC SSO means members can **only** access Infisical through the identity provider.
Two further effects, both tied to the verified email domain:

1. **Email and password signup is blocked for your verified domains.** New password accounts cannot
   be created for addresses on those domains. This is deliberate — a competing password account would
   reopen an account-takeover vector against an address the IdP is supposed to own.
2. **Email verification is skipped for SSO sign-ins.** The verified domain plus the IdP already prove
   ownership of the address, so the extra verification step is unnecessary.

### The pre-enforcement checklist

**Before enabling enforcement**, confirm:

- A **break-glass organization admin** exists, with a **password** set
- That admin knows about `/login/admin`
- SSO login has been **tested end to end** by a real user

The signup block is what makes this urgent: after enforcement you cannot create a new password
account on the verified domain to recover with. Get the escape hatch in place first.

## Break-glass: the admin login portal

If the SSO provider goes down, **Organization Admins** can bypass enforcement through the Admin
Login Portal:

```
https://app.infisical.com/login/admin
```

(Substitute your own domain when self-hosting.)

Two constraints:

- You must be an **Organization Admin for that specific organization**
- **Server Admin status alone does not grant this.** The two roles are independent, and this catches people out on self-hosted instances where an operator assumes server-level admin covers everything

Document this URL somewhere reachable **without** logging into Infisical. A break-glass procedure
recorded only inside the system it recovers is not a procedure.

## Recommended rollout order

1. Verify the email domain
2. Configure the IdP side (metadata, certificate, or client credentials)
3. Configure the Infisical side
4. **Test login** with a real user account
5. Confirm a break-glass org admin has a password
6. Set up SCIM if you want provisioning — see `references/scim-and-groups.md`
7. Configure group mapping and role assignment
8. **Only then** enable enforcement

Enforcement last. Every step before it is reversible; enforcement is the one that can lock you out.

## Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| Users cannot log in via SSO at all | Email domain not verified |
| SCIM cannot be enabled | SAML/OIDC not configured yet, or domain unverified |
| Cannot create a password account for a colleague | SSO enforcement blocks signup on verified domains — expected |
| Locked out after enforcement | Use `/login/admin` as an Organization Admin |
| Group memberships are stale | Group mapping only syncs at login — see `references/scim-and-groups.md` |
| Manual group edits are rejected | Group mapping is enabled, which disables manual management |
