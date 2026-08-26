Quick note: I don't have live web access in this session, so I can't pull the current Infisical docs page directly — this answer is from my knowledge as trained (through Jan 2026) and I'd recommend a quick cross-check against docs.infisical.com since Infisical adds auth methods somewhat regularly.

**Auth method for Alibaba Cloud: Alicloud Auth (Alibaba Cloud Auth)**

It works the same way Infisical's AWS Auth does: your workload (ECS instance, container, function, etc.) uses its RAM credentials to sign an STS `GetCallerIdentity`-style request. It sends that signed request to Infisical, which replays it against Alibaba Cloud's STS API to confirm the caller's RAM identity, then checks the resulting ARN against an allow-list on the Infisical machine identity.

**What to configure on the identity**
- Add "Alicloud Auth" as an auth method on the machine identity
- **Allowed ARN** — the RAM role/user ARN(s) permitted to authenticate as this identity (wildcards supported)
- Standard access-token settings shared across all auth methods: Access Token TTL, Max TTL, Max Number of Uses, and Trusted IPs

**Login endpoint**
```
POST /api/v1/auth/alicloud-auth/login
```
against your Infisical instance (`https://app.infisical.com` for Cloud, or your self-hosted domain). The workload posts its signed STS `GetCallerIdentity` request details (method, URL, headers, body); Infisical validates it and returns an access token if the ARN matches your allow-list.

**Total machine identity auth methods**

By my count, Infisical supports 12: Universal Auth, Token Auth, Kubernetes Auth, AWS Auth, Azure Auth, GCP Auth, OCI Auth, Alicloud Auth, JWT Auth, OIDC Auth, TLS Certificate Auth, and LDAP Auth.

Given I can't verify live right now, I'd treat the exact endpoint path and total count as "confirm before shipping" — worth a quick check against `docs.infisical.com/documentation/platform/identities` before you wire it up.
