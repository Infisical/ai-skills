Alibaba Cloud isn't one of the platform-specific zero-secret options in Infisical's auth method lineup, so the recommended choice is **Universal Auth** (the general-purpose fallback that works on any platform).

## Setup on the machine identity

1. Add Universal Auth to the identity (this is the default auth method).
2. Configure:
   - Access Token TTL
   - Max TTL
   - Max Number of Uses
   - Trusted IPs
3. Create a Client Secret for it (can have its own TTL and usage limits).
4. Hand the Client ID and Client Secret to your workload running on Alibaba Cloud.

Note the lockout protection: 3 failed login attempts in 30 seconds triggers a 5-minute lockout (configurable).

## Login endpoint

```
POST /api/v1/auth/universal-auth/login
{ "clientId": "<id>", "clientSecret": "<secret>" }
→ { "accessToken": "<short-lived-token>" }
```

CLI equivalent:
```bash
infisical login --method=universal-auth --client-id=<id> --client-secret=<secret>
```

## Total auth methods

Infisical supports **10 machine identity auth methods**: Universal Auth, AWS Auth, Kubernetes Auth, GCP Auth, Azure Auth, OIDC Auth, Token Auth, SPIFFE Auth, TLS Certificate Auth, and LDAP Auth.

If your Alibaba Cloud workload can present an OIDC token (some Alibaba services support OIDC-based workload identity), OIDC Auth could also be worth checking against Infisical's docs directly, since this reference doesn't call out Alibaba specifically. Otherwise, Universal Auth is the safe, works-everywhere choice.
