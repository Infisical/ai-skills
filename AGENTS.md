# Infisical AI Skills

17 skills covering the Infisical platform. **Read the router below before loading a skill** — several
skills cover adjacent concepts that are easy to confuse, and loading the wrong one produces
confidently wrong answers.

## Router: pick a skill from the user's intent

| The user wants to... | Skill |
|----------------------|-------|
| Get secrets into an app, container, CLI, CI/CD, or via an SDK | `infisical-setup` |
| Call the REST API directly | `infisical-api` |
| Use Terraform / HCL | `infisical-terraform` |
| Render secrets to a **file**, or run a sidecar/init container | `infisical-agent` |
| Sync secrets into **Kubernetes** Secrets/ConfigMaps | `infisical-kubernetes-operator` |
| **Push** secrets out to a third-party service | `infisical-secret-syncs` |
| Authenticate Infisical **out** to a third party | `infisical-app-connections` |
| Get a **brand-new short-lived** credential per request | `infisical-dynamic-secrets` |
| **Change an existing** credential on a schedule | `infisical-secret-rotation` |
| Let a **human or AI agent** reach infrastructure, recorded, without a credential | `infisical-pam` |
| Issue or manage **X.509 / TLS certificates**, or sign code | `infisical-pki` |
| **Encrypt / sign data** with a managed key | `infisical-kms` |
| Find **leaked credentials** in source code | `infisical-secret-scanning` |
| Configure **human login** (SAML/OIDC/LDAP) or SCIM provisioning | `infisical-sso` |
| Define **roles, permissions, approvals**, or stream audit logs | `infisical-access-control` |
| Reach a resource with **no public endpoint** | `infisical-gateway` |
| **Deploy Infisical itself** | `infisical-self-host` |

## Disambiguation: the pairs that get confused

Check these before answering. Each pair looks similar and routes differently.

| Sounds like | Actually two things |
|-------------|--------------------|
| "temporary credentials" | **Dynamic secrets** create a new credential per lease. **Secret rotation** changes one existing credential on a timer. New vs existing. |
| "give someone database access" | **PAM** brokers a recorded session and never reveals the credential. **Dynamic secrets** hand a real credential to a workload. Human/agent vs application. |
| "connect Infisical to AWS" | **App Connection** = Infisical authenticating *outward*. **Machine identity** = a workload authenticating *inward*. Check the direction. |
| "OIDC" / "LDAP" | **`infisical-sso`** for humans logging in. **`infisical-setup`** for machine identity auth. Also an LDAP **App Connection** and LDAP **dynamic secrets**. Four unrelated things. |
| "certificates" | **`infisical-pki`** for X.509/TLS. **`infisical-dynamic-secrets`** for SSH certificates. SSH is not in the PKI product. |
| "sync" | **Secret Syncs** push secrets. **PKI Syncs** push certificates — a separate feature in `infisical-pki`. |
| "install the Helm chart" | `secrets-operator` chart = the **operator** (`infisical-kubernetes-operator`). The standalone chart = **the platform** (`infisical-self-host`). |
| "rotation" | **Secret Rotation** writes new values into secrets. **App Connection credential rotation** refreshes Infisical's own stored credential and writes nothing. **PAM account rotation** is a third thing. |
| "approval" | Secrets → `infisical-access-control`. Infrastructure sessions → `infisical-pam`. Certificate issuance or code signing → `infisical-pki`. |
| "encryption key" | **`infisical-kms`** to hold a key and do the crypto. **`infisical-setup`** if they just want to store key material as a secret. |

## Shared prerequisites

Several features depend on another being set up first. Check the dependency before debugging.

| Feature | Requires |
|---------|----------|
| Secret Sync | An **App Connection** of the matching type |
| Secret Rotation | An **App Connection** of the matching type |
| PKI external CA / PKI Sync | An **App Connection**, usually plus a **Gateway** |
| Secret Scanning data source | An App Connection — **`github-radar`**, not `github`, for GitHub |
| Anything reaching a private network | A **Gateway** (only 16 connection types accept one) |
| SCIM provisioning | Email domain verification **and** SAML/OIDC already configured |
| Any SSO login | Email domain verification |
| HSM-backed keys | A **Gateway** in the HSM's network |

## Skills

### infisical-setup
Getting secrets into applications and platforms. CLI, all 9 SDKs (Node.js, Python, Go, Java, .NET,
Ruby, PHP, Rust, C++), Docker, CI/CD, and all 13 machine identity auth methods.

### infisical-api
The REST API: `/api/v4/secrets` CRUD and batch operations, projects, identities, all 13 auth-method
login endpoints, which endpoints paginate and which do not, rate limits.

### infisical-terraform
The Infisical Terraform provider: the nested `auth = { universal | oidc }` block, ephemeral resources
keyed by `name`, data sources, project roles, Terraform Cloud OIDC.

### infisical-agent
The Agent daemon: YAML config, 6 agent auth methods, Go template functions including the
SSH-required `principals` argument, sinks, polling, on-change commands, caching.

### infisical-kubernetes-operator
The operator: v1beta1 CRDs (`InfisicalConnection`, `InfisicalAuth`, `InfisicalStaticSecret`) and
legacy v1alpha1 (`InfisicalSecret`, `InfisicalDynamicSecret`, `InfisicalPushSecret`), Helm install,
`auto-reload`, templating.

### infisical-secret-syncs
Pushing secrets to all 48 destinations. App Connections, key schemas, initial-sync enum values,
mapping behavior (AWS Secrets Manager only), provider quirks.

### infisical-app-connections
All 83 connection types and their exact auth methods, platform-managed credentials, Gateway-routed
connections, connection-level credential rotation. The shared prerequisite for syncs, rotations,
PKI, and scanning.

### infisical-dynamic-secrets
On-demand short-lived credentials across all 30 providers. Lease lifecycle, TTLs, creation
statements, SSH certificates, Gateway setup for private networks.

### infisical-secret-rotation
Rotating existing credentials across 28 providers. Dual-phase vs single-phase, the two-user pattern
for SQL, `rotationInterval` and `rotateAtUtc`, parameters and `secretsMapping`.

### infisical-pam
Brokered privileged access for humans and AI agents across 13 account types. Accounts, folders,
templates, memberships, session recording, just-in-time approvals, agentic access.

### infisical-pki
Certificate Management: 9 CA types, Policies/Profiles/Applications, 4 enrollment methods
(API/ACME/EST/SCEP), 12 PKI Syncs, code signing, HSM connectors, post-quantum algorithms.

### infisical-kms
Managed cryptographic keys: the 3 key usages, symmetric/asymmetric/HMAC algorithms, encrypt,
decrypt, sign, verify, MAC, rotation, external KMS, KMIP, cosign.

### infisical-secret-scanning
Detecting leaked credentials: 3 cloud data sources, full vs diff scans, finding lifecycle, the
`infisical scan` CLI and pre-commit hooks, noise reduction, AWS honey tokens.

### infisical-access-control
Governance: org and project roles, custom roles, the granular secret actions that separate
`describeSecret` from `readValue`, ABAC, temporary access, approval policies, audit log streams.

### infisical-sso
Human login and provisioning: SAML/OIDC/LDAP plus free Google/GitHub SSO, SCIM, group-to-role
mapping, SSO enforcement and the `/login/admin` break-glass portal.

### infisical-gateway
Reaching private networks: the gateway/relay architecture, exact ports and egress rules, deployment,
Gateway Pools for HA, and which features can be routed through one.

### infisical-self-host
Deploying Infisical: Docker, Docker Compose, Kubernetes Helm, environment variables, Redis
requirements including the mandatory `noeviction` policy, FIPS 140-3, scaling and HA.

## Maintaining these skills

Skill content is a vendored snapshot of a moving codebase. An audit found that **a drifted skill
performs worse than no skill at all** — stale specifics override correct model knowledge. See
`evals/accuracy-audit-2026-08/`.

When re-verifying, read the **code**, not the docs prose. Counts and enum values live in:

| Fact | Source |
|------|--------|
| Secret syncs | `backend/src/services/secret-sync/secret-sync-enums.ts` |
| Secret rotations | `backend/src/ee/services/secret-rotation-v2/secret-rotation-v2-enums.ts` |
| Dynamic secret providers | `backend/src/ee/services/dynamic-secret/providers/models.ts` |
| App Connections | `backend/src/services/app-connection/app-connection-enums.ts` |
| Machine identity auth methods | `backend/src/db/schemas/models.ts` (`IdentityAuthMethod`) |
| PAM account types | `backend/src/ee/services/pam/pam-enums.ts` |
| CA types | `backend/src/services/certificate-authority/certificate-authority-enums.ts` |
| PKI syncs | `backend/src/services/pki-sync/pki-sync-enums.ts` |
| KMS algorithms | `backend/src/lib/crypto/{cipher,sign,hmac}/types.ts` |
| Permissions | `backend/src/ee/services/permission/{org,project}-permission.ts` |
| API routes | `backend/src/server/routes/` |

Also: `plugins/<name>/skills/<name>/` is a **copy** of `skills/<name>/`. They drift silently — diff
them before committing.
