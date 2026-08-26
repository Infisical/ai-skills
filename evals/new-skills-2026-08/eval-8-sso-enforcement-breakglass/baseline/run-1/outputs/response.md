Before flipping SAML enforcement on, the main thing is proving the SSO path actually works end-to-end, since enforcement removes your fallback.

**Do first:**

1. Fully configure and test SAML (IdP metadata, ACS URL, certificate, attribute mapping) and have at least one real, non-admin user successfully log in through it. Don't enforce based on a config you've only validated in theory.
2. Confirm there's a break-glass path for org admins. Most platforms that support SSO enforcement, Infisical included, need some way for an admin to regain access if the IdP has an outage or misconfiguration. Check the current org settings for this explicitly rather than assuming it exists, since I can't verify the current UI/behavior from here.
3. Audit non-interactive auth paths. Service tokens, machine identities, and any integrations that currently authenticate with username/password need to already be migrated to token-based or machine identity auth, since password login being disabled will break them too.
4. Confirm role/group mapping from the IdP is correct, so users land with the right permissions after their first SSO login rather than needing manual fixing.
5. Give members a heads-up before cutover so they're not locked out mid-workday without warning.

**Risks:**

- **Lockout**: if the IdP has an outage, misconfiguration, or you mistype something in the SAML setup, and there's no working break-glass account, nobody, including admins, can get in.
- **Single point of failure**: your IdP now gates access to all your secrets in Infisical. An IdP outage becomes an Infisical outage.
- **Broken automation**: anything still authenticating with a password (scripts, old integrations) stops working the moment you enforce.
- **Silent rollback difficulty**: if the person who enabled enforcement is also the one who gets locked out, there may be no self-service way to undo it.

Given the blast radius here, I'd treat this as a change to test in a non-critical org or with a single test user first, not something to flip directly on your production org. Since I don't have live access to Infisical's current docs or dashboard in this session, I'd double check the exact enforcement toggle and break-glass behavior in your current admin settings before proceeding, rather than relying on my recollection of it.
