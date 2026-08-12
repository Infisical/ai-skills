# SCIM Provisioning and Group Mapping

## Why provisioning matters more than SSO

SSO controls **login**. Provisioning controls **existence**.

Without provisioning, an offboarded employee's Infisical account still exists — they simply cannot log
in through the IdP. With SCIM deprovisioning, the account is removed. For offboarding you want both:
SSO to close the door, SCIM to remove the key.

That distinction is worth making explicitly when a user thinks SSO alone has solved access
management.

## SCIM

**Paid — Enterprise tier** on Cloud, or an enterprise license self-hosted.

### Prerequisites

Two, both hard requirements:

1. **Email Domain Verification** completed
2. **SAML or OIDC already configured** for the organization

SCIM cannot be enabled before SSO exists. If a user cannot find the SCIM option, check these before
looking at the provider.

### Supported providers

| Provider | Doc |
|----------|-----|
| Okta | `scim/okta` |
| Azure / Entra ID | `scim/azure` |
| JumpCloud | `scim/jumpcloud` |
| PingOne | `scim/pingone` |
| PingFederate | `scim/pingfederate` |

Provisions and deprovisions both **users and user groups**.

## SCIM group to organization role mappings

By default, SCIM-provisioned users receive the **default organization role** configured in
Organization General Settings.

For finer control, configure **SCIM Group to Organization Role Mappings**, which assign a role based
on the group a user is provisioned from.

This is the mechanism that makes provisioning genuinely hands-off: create the right groups in the
IdP, map each to a role, and a new joiner lands with correct access without anyone touching
Infisical.

Set the default organization role to something **minimal** — ideally `no-access` or `member` — and let
group mappings grant more. If the default is generous, anyone provisioned outside a mapped group gets
more access than intended.

## Group membership mapping (SAML / OIDC)

Separate from SCIM. Syncs group membership **at login** based on what the IdP asserts.

### OIDC

Configure a **`groups` claim** on your provider's tokens. On login, the user is:

- **Added** to Infisical groups present in their `groups` claim
- **Removed** from any Infisical group **not** present in the claim

Available for general OIDC providers and with a Keycloak-specific guide (Keycloak calls it a group
membership mapper).

### The two constraints that matter

**1. Membership only syncs at login.**

> Removing a user from a group in the IdP is **not** reflected in Infisical until their next SSO
> login.

This is the most consequential limitation. Revoking access by removing someone from an IdP group does
nothing immediately — their existing Infisical session and group memberships persist.

The documented mitigation is to **enable Enforce SSO**, which forces re-authentication through the IdP
and so brings the sync forward. Combine that with:

- **SCIM deprovisioning** for actual offboarding, which does not wait for a login
- **Short session lifetimes** so the next login comes sooner

If a user asks "how do I immediately revoke someone's access," group mapping is the wrong answer.
Remove the membership in Infisical directly, or deprovision via SCIM.

**2. Enabling group mapping disables manual group management.**

> When enabled, manual management of Infisical group memberships is disabled.

The IdP becomes the sole authority. Before enabling it, confirm every group anyone depends on exists
in the IdP with the right members — otherwise turning it on empties groups at the next login and
people lose access.

Migration order:

1. Create matching groups in the IdP with correct membership
2. Verify names match Infisical group names exactly
3. Then enable mapping

## GitHub Team Sync

A separate mechanism for organizations using GitHub SSO. Syncs **GitHub teams** to Infisical groups:
users logging in via GitHub are added to or removed from Infisical groups based on their team
memberships in the specified GitHub organization.

Configure it on the **Single Sign-On (SSO)** page under the **Provisioning** tab, supplying your
GitHub organization name.

Same login-time caveat applies — team changes take effect at next login.

Good fit for engineering-led organizations already managing access through GitHub teams, without
needing a paid IdP integration.

## Putting it together

The target state for a mature setup:

```
IdP groups  --SCIM-->  Infisical groups  --role assignment-->  permissions
    |                                                              |
    +--> SSO login (SAML/OIDC), enforced                           |
                                                                   v
                                       Access follows group membership,
                                       joiners/leavers handled by the IdP
```

Steps:

1. Verify the email domain
2. Configure SAML or OIDC and **test** it
3. Ensure a break-glass org admin has a password (see `references/sso-setup.md`)
4. Enable SCIM for user and group provisioning
5. Create IdP groups mirroring how access should work
6. Map SCIM groups to organization roles
7. Assign **project** roles to those groups — see `infisical-access-control`
8. Set the default organization role to something minimal
9. Enable SSO enforcement

The payoff: onboarding and offboarding happen entirely in the IdP. Nobody edits Infisical membership
by hand, which is also what makes the access model auditable.

## Troubleshooting

| Symptom | Cause |
|---------|-------|
| SCIM option unavailable | Domain unverified, or SAML/OIDC not configured |
| Users provisioned with too much access | Default organization role is too generous; set it minimal and use group mappings |
| Removed from a group in the IdP but still has access | Group mapping syncs at login only. Enforce SSO, or remove directly / deprovision via SCIM |
| Manual group changes rejected | Group mapping is enabled and owns membership |
| Groups empty after enabling mapping | IdP group names do not match Infisical group names |
