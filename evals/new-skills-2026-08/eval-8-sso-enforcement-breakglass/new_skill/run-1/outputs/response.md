Before enabling SAML enforcement, do these in order:

**1. Verify your email domain** (if not already done)
Required for SSO and gates everything else.

**2. Configure SAML and test it end-to-end**
Set up the IdP side (metadata/certificate) and the Infisical side, then have a real user actually log in through it. Don't skip this.

**3. Create a break-glass Organization Admin with a password set**
This is the critical step. Once enforcement is on, you cannot create new password accounts on your verified domain, so you need at least one admin account that already has a password before you flip the switch.

**4. Make sure that admin knows about `/login/admin`**
This is the Admin Login Portal (`https://app.infisical.com/login/admin`, or your self-hosted domain equivalent) — the bypass route if the SAML IdP ever goes down. Two things to watch:
- Only works for someone who is an **Organization Admin for that specific org**
- **Server Admin status does not count** — that's a separate role, and it's a common trap on self-hosted instances

Document that URL somewhere reachable *without* logging into Infisical (wiki, runbook, etc.) — a break-glass procedure stored only inside the system it's meant to rescue you from isn't one.

### The risk

Enforcing SAML **blocks email/password signup for your verified domains**. This is intentional (stops someone spinning up a competing password account on an address the IdP is supposed to own), but it means: after enforcement, there's no way to create a fresh password account to recover with. Your only way back in if SAML breaks is an existing break-glass admin using `/login/admin`. If you enable enforcement without one, you can lock your whole org out of Infisical.

### Recommended order
1. Verify email domain
2. Configure SAML (IdP + Infisical)
3. Test login with a real user
4. Confirm break-glass admin has a password and knows `/login/admin`
5. **Then** enable enforcement

One more note since you said "so nobody can log in with a password" — if you also want offboarding to actually remove accounts (not just block login), SSO enforcement alone doesn't do that. You'd want SCIM provisioning too, which is a separate Enterprise-tier feature and requires SAML to already be configured first. Let me know if you want to cover that as well.
