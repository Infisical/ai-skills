# Issuance, Profiles, and Enrollment

## Policies, Profiles, Applications

The chain of responsibility, and who touches what:

| Object | Created by | Purpose |
|--------|-----------|---------|
| **Certificate Policy** | Product Admin | The rules: allowed algorithms, key usages, TTL bounds, subject constraints |
| **Certificate Profile** | Product Admin | A CA + a Policy + defaults. The reusable "shape" of a certificate |
| **Application** | Product Admin | A service or fleet. Profiles are attached to it; teams work inside it |
| **Enrollment method** | Application Admin | How clients request certs, configured on a profile attached to the Application |

Why this split exists: teams get to request certificates without understanding PKI, because the
profile already encodes the guardrails. Without profiles every team configures CA, policy, TTL, and
algorithms by hand and misconfiguration is inevitable.

Consequence for answering questions: **you do not issue certificates from a CA directly.** Create a
Policy and Profile, attach the Profile to an Application, then issue through the Application.

### Application roles

Members hold **Admin**, **Operator**, or **Auditor** on an Application. Product Admins create
Applications and assign members; teams then operate independently inside them.

### What lives on an Application

- Members and their roles
- Enrollment methods (API, ACME, EST, SCEP)
- The certificate inventory
- Alerting for expiration, issuance, renewal, revocation
- Optional approval policies gating issuance
- Certificate syncs to external destinations

## The 4 enrollment methods

`EnrollmentType` values: `api`, `acme`, `est`, `scep`.

Choose by **what the client can speak**, not by preference:

| Method | Use when | Client generates key? |
|--------|----------|----------------------|
| `api` | You control the requesting code; scripts, CI, custom services | Either |
| `acme` | Web servers, cert-manager, Caddy, Traefik — anything with an ACME client | Yes |
| `est` | Enterprise devices, IoT, network gear with bootstrap certificates | Yes |
| `scep` | Legacy MDM, Windows/Intune device enrollment, older network appliances | Yes |

For ACME, EST, and SCEP the **client** generates the key pair and sends a CSR. Infisical never sees
the private key. Do not promise users a downloadable private key on those flows.

### API enrollment

Straightforward request/response against the Infisical API. Use it for CI pipelines, provisioning
scripts, and services you own. This is the only method where Infisical can generate the key pair and
return it, if you want that.

### ACME enrollment

Infisical acts as an ACME **server** here — the inverse of an ACME CA, where Infisical is the
client. Clients complete an HTTP-01 challenge at `/.well-known/acme-challenge/`.

Point any standard ACME client at the profile's ACME directory URL. This is the path of least
resistance for Kubernetes (`cert-manager`), nginx/Caddy, and Traefik.

### EST enrollment

Enrollment over Secure Transport (RFC 7030). Mutual TLS: the device authenticates with a
pre-installed bootstrap certificate.

Endpoints, note **port 8443**:

```
https://app.infisical.com:8443/.well-known/est/{profile-id}/cacerts
https://app.infisical.com:8443/.well-known/est/{profile-id}/simpleenroll
https://app.infisical.com:8443/.well-known/est/{profile-id}/simplereenroll
```

| Endpoint | Purpose |
|----------|---------|
| `cacerts` | Retrieve the CA chain |
| `simpleenroll` | Initial certificate request |
| `simplereenroll` | Renewal |

The `{profile-id}` in the path is the Certificate Profile's ID. EST runs on a **separate port
(8443)**, which is a common source of connectivity failures — firewalls that allow 443 often block
it.

EST assumes devices already hold a bootstrap credential. If they do not, EST is not viable and SCEP
with a challenge password may be the fallback.

### SCEP enrollment

Simple Certificate Enrollment Protocol, for legacy and MDM-driven enrollment.

Endpoints:

```
https://app.infisical.com/scep/{profile_id}/pkiclient.exe
https://app.infisical.com/scep/{profile_id}/challenge
```

`pkiclient.exe` is not a Windows binary — it is the conventional SCEP endpoint name, and every SCEP
client expects it. Do not "fix" it.

SCEP operations:

| Operation | Purpose |
|-----------|---------|
| `GetCACert` | Returns the RA certificate and CA chain as a PKCS#7 bundle |
| `PKIOperation` | Handles `PKCSReq` (enrollment), `RenewalReq` (renewal), and `GetCertInitial` (polling) |

**Challenge password modes** — how a device proves it is allowed to enroll:

| Mode | Behavior |
|------|----------|
| Static password | One shared password for every device on the profile. Simplest. **Minimum 8 characters** |
| Microsoft Intune | The challenge is validated against Intune rather than a stored password. Intune generates a unique challenge per device and Infisical asks Intune to confirm it |
| One-time-use | Challenges are minted on demand through an authenticated API endpoint. Each is single-use with a configurable expiry |

Intune mode is the right answer for Windows fleets already managed by Intune — it gives per-device
challenges without you distributing anything. It requires a `microsoft-intune` App Connection.

One-time-use is the best choice when you script enrollment and can fetch a challenge per device.
Static is acceptable only where the device population is trusted and closed.

## Key algorithms

See `references/certificate-authorities.md` for the full table. The trap worth repeating:

- ECDSA P-256 is **`EC_prime256v1`**, not `ECDSA_P256`
- ECDSA P-384 is **`EC_secp384r1`**
- ECDSA P-521 is **`EC_secp521r1`**

RSA values (`RSA_2048`, `RSA_3072`, `RSA_4096`) and PQC values (`ML-DSA-44`, `SLH-DSA-SHA2-128f`,
etc.) are literal.

## Key usages

`CertKeyUsage` — camelCase, matching the X.509 names:

`digitalSignature`, `keyEncipherment`, `nonRepudiation`, `dataEncipherment`, `keyAgreement`,
`keyCertSign`, `cRLSign`, `encipherOnly`, `decipherOnly`

Note `cRLSign` — lowercase `c`, uppercase `RLS`. That is the correct X.509 spelling and it looks
like a typo.

Typical combinations:

| Certificate purpose | Key usages |
|--------------------|-----------|
| TLS server | `digitalSignature`, `keyEncipherment` |
| TLS client (mTLS) | `digitalSignature`, `keyEncipherment` |
| A CA | `keyCertSign`, `cRLSign` |
| Signing only | `digitalSignature`, `nonRepudiation` |

## Extended key usages

These have **two spellings** and both appear in the platform:

| Purpose | Standard value | Legacy value | OID |
|---------|---------------|--------------|-----|
| Client auth | `client_auth` | `clientAuth` | 1.3.6.1.5.5.7.3.2 |
| Server auth | `server_auth` | `serverAuth` | 1.3.6.1.5.5.7.3.1 |
| Code signing | `code_signing` | `codeSigning` | 1.3.6.1.5.5.7.3.3 |
| Email protection | `email_protection` | `emailProtection` | 1.3.6.1.5.5.7.3.4 |
| OCSP signing | `ocsp_signing` | `ocspSigning` | 1.3.6.1.5.5.7.3.9 |
| Time stamping | `time_stamping` | `timeStamping` | 1.3.6.1.5.5.7.3.8 |
| Any purpose | `any_purpose` | `anyExtendedKeyUsage` | 2.5.29.37.0 |

Snake_case is the current form; the camelCase names are accepted as legacy aliases. If a user
reports an EKU value being rejected, check which form the endpoint expects rather than assuming the
value is wrong.

Note `time_stamping` maps to legacy `timeStamping`, and `any_purpose` maps to
`anyExtendedKeyUsage` — not `anyPurpose`.

## Certificate lifecycle

`CertStatus` is `active`, `expired`, or `revoked`.

Policies can mark fields as `mandatory`, `optional`, or `prohibit` — that is how a profile forces a
SAN to be present, or forbids a wildcard.

### Renewal

Configure automatic renewal on the Application. The cardinal rule of PKI operations: the failure is
always an expiry nobody was watching. Set up renewal **and** alerting in the same sitting as
issuance.

For ACME/EST/SCEP, renewal is client-driven — the client re-enrolls
(`simplereenroll`, `RenewalReq`, or an ACME renewal) before expiry. Infisical will not push a new
certificate to a device that does not ask.

### Revocation

Revoking marks the certificate `revoked` and publishes it to the CRL. This only affects clients that
actually check the CRL, and only after they refresh it. Prefer short TTLs plus automated renewal
over depending on revocation — see the CRL section in `references/certificate-authorities.md`.

### Approvals

An Application can require approval before issuance. Use it for high-value certificates —
wildcards, long-lived certs, anything for a production public domain. Approval policy mechanics
mirror the change-approval model in `infisical-access-control`.

## Certificate discovery

Infisical can scan your network to find certificates it did not issue, which is how you find the
expiring cert on a forgotten load balancer. Useful when migrating onto Infisical: discover first,
then bring what you find under management.
