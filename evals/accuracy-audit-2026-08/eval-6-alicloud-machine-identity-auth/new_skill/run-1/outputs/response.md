Based on the skill reference, here's what applies to Alibaba Cloud:

## Auth method: AliCloud Auth

## Configuration on the identity
1. Add **AliCloud Auth** to the machine identity
2. Configure **Allowed ARNs** — a comma-separated list of trusted Alibaba Cloud ARNs

The client signs a request with its Alibaba Cloud RAM credentials, and Infisical verifies that identity with Alibaba Cloud, checking it against the allowlist you configure.

## Login endpoint
```
POST /api/v1/auth/alicloud-auth/login
```

## Total auth methods
Infisical supports **13** machine identity auth methods total: Universal, Token, Kubernetes, GCP, AliCloud, AWS, Azure, TLS Cert, OCI, OIDC, JWT, LDAP, and SPIFFE.

Note that AliCloud Auth isn't zero-secret in the strictest sense (unlike, say, Kubernetes or AWS Auth) — it authenticates a RAM user account, so the workload still needs access to Alibaba Cloud credentials to sign the request, but nothing Infisical-specific needs to be stored on the machine itself.
