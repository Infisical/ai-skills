# Certificate Authorities

## The 9 CA types

`type` values, exactly as the API accepts them:

| CA type | `type` value | Trust | Needs App Connection |
|---------|-------------|-------|---------------------|
| Internal | `internal` | Private — Infisical holds the signing key | No |
| ACME | `acme` | Public (Let's Encrypt etc.) or private ACME | Yes, for DNS-01 |
| AWS Private CA | `aws-pca` | Private, AWS-hosted | Yes (`aws`) |
| AWS ACM Public CA | `aws-acm-public-ca` | Public | Yes (`aws`) |
| Microsoft ADCS | `adcs` | Private, on-premises | Yes (`adcs`) |
| Azure ADCS (Web Enrollment) | `azure-ad-cs` | Private | Yes (`azure-adcs`) |
| DigiCert | `digicert` | Public | Yes (`digicert`) |
| Venafi TPP | `venafi-tpp` | Private, Venafi-managed | Yes (`venafi-tpp`) |
| GoDaddy | `godaddy` | Public | Yes (`godaddy`) |

Note the Azure ADCS type value is `azure-ad-cs` (three segments) while its App Connection slug is
`azure-adcs` (two). They do not match — a genuine inconsistency worth remembering.

## Choosing a CA

| The user needs certificates for... | Use |
|-----------------------------------|-----|
| Internal services, mTLS between workloads, IoT fleets | Internal CA |
| Public websites, anything a browser must trust for free | ACME with Let's Encrypt |
| Public certs with an existing commercial vendor | DigiCert, GoDaddy, or AWS ACM Public CA |
| Anything where an on-prem Microsoft CA is already authoritative | ADCS or Azure ADCS |
| An organization standardized on Venafi | Venafi TPP |
| AWS-native private PKI | AWS Private CA |

Default to an **Internal CA** for private/internal use. It is the only option with no external
dependency, and it is the only one that supports post-quantum key algorithms.

## Internal CA

### Status matters

`status` is one of:

| Status | Meaning |
|--------|---------|
| `active` | Has a certificate, can issue |
| `disabled` | Exists but will not issue |
| `pending-certificate` | **No certificate yet — cannot issue anything** |

An intermediate CA sits in `pending-certificate` between creation and having its CSR signed. If a
user reports "my CA won't issue," check status first.

### Root and intermediate

`InternalCaType` is `root` or `intermediate`.

- A **root** CA self-signs. It is the trust anchor you distribute to clients.
- An **intermediate** CA is signed by a parent (an Infisical root, or an external CA).

Recommended hierarchy: one root, kept long-lived and rarely touched, signing one or more
intermediates that do the day-to-day issuing. Issuing leaf certificates directly from a root means
a root key compromise forces you to re-establish trust everywhere.

Creating an intermediate signed by an Infisical root:

1. Create the root CA (self-signs, becomes `active`)
2. Create the intermediate CA — it starts `pending-certificate` and produces a CSR
3. Sign that CSR with the root
4. Import the signed certificate back onto the intermediate; it becomes `active`

For an intermediate signed by an **external** CA, export the CSR at step 2, get it signed out of
band, and import the result at step 4.

### Key algorithms

`CertKeyAlgorithm` values. **The wire value is not always the obvious name:**

| Algorithm | Wire value |
|-----------|-----------|
| RSA 2048 | `RSA_2048` |
| RSA 3072 | `RSA_3072` |
| RSA 4096 | `RSA_4096` |
| ECDSA P-256 | **`EC_prime256v1`** |
| ECDSA P-384 | **`EC_secp384r1`** |
| ECDSA P-521 | **`EC_secp521r1`** |
| ML-DSA-44 (PQC, NIST L2) | `ML-DSA-44` |
| ML-DSA-65 (PQC, NIST L3) | `ML-DSA-65` |
| ML-DSA-87 (PQC, NIST L5) | `ML-DSA-87` |
| SLH-DSA-SHA2-128f | `SLH-DSA-SHA2-128f` |
| SLH-DSA-SHA2-128s | `SLH-DSA-SHA2-128s` |
| SLH-DSA-SHA2-192f | `SLH-DSA-SHA2-192f` |
| SLH-DSA-SHA2-192s | `SLH-DSA-SHA2-192s` |
| SLH-DSA-SHA2-256f | `SLH-DSA-SHA2-256f` |

The ECDSA values use OpenSSL curve names, not NIST names. `ECDSA_P256` is the internal enum *key*
and is rejected as a value.

### Post-quantum algorithms

- **ML-DSA** (FIPS 204, formerly CRYSTALS-Dilithium) — lattice-based. The recommended PQC choice for most uses: good balance of key size and performance.
- **SLH-DSA** (FIPS 205, formerly SPHINCS+) — hash-based, more conservative security assumptions, much larger signatures. The `f` variants optimize signing speed, the `s` variants optimize signature size.

Selectable from the Key Algorithm dropdown when creating an Internal CA. Worth recommending for a
long-lived root, whose lifetime may outlast classical assumptions. Verify client support before
using PQC on leaf certificates — many TLS stacks do not yet handle these.

## ACME CAs

For ACME-protocol CAs, including Let's Encrypt. Infisical acts as the ACME client and completes
**DNS-01** challenges by writing TXT records through an App Connection.

Configuration fields:

| Field | Description |
|-------|-------------|
| `directoryUrl` | The ACME directory endpoint |
| `accountEmail` | Contact email for the ACME account |
| `dnsAppConnectionId` | App Connection used to write DNS challenge records |
| `dnsProviderConfig.provider` | `route53`, `cloudflare`, `dns-made-easy`, or `azure-dns` |
| `dnsProviderConfig.hostedZoneId` | The zone in which to write records |
| `eabKid` | External Account Binding key ID, if the CA requires EAB |
| `eabHmacKey` | External Account Binding HMAC key |
| `dnsResolver` | Optional custom resolver for challenge verification |

Supported DNS providers for DNS-01: **Route53, Cloudflare, DNS Made Easy, Azure DNS**. Only these
four. If the user's DNS is elsewhere, ACME through Infisical will not work — say so rather than
improvising.

The challenge record written is `_acme-challenge`.

EAB (`eabKid` + `eabHmacKey`) is required by some ACME providers, notably ZeroSSL and Google Trust
Services. Let's Encrypt does not require it.

## External CAs

`adcs`, `azure-ad-cs`, `venafi-tpp`, `digicert`, `aws-pca`, `aws-acm-public-ca`, `godaddy`.

Two things they all need:

1. **An App Connection** of the matching type — see `infisical-app-connections`
2. Often **a Gateway**, because ADCS, Azure ADCS, and Venafi TPP typically live on internal networks with no public endpoint. Those three connection types support `gatewayId`. See `infisical-gateway`

With an external CA, Infisical orchestrates issuance and tracks lifecycle but the third party
signs. Constraints imposed by that CA (name policies, validity limits, approval steps) still apply
and Infisical cannot override them.

## CA renewal

Certificate authorities expire too, and a root expiring is far more disruptive than a leaf.

`CaRenewalType` is `existing` — renewing reuses the existing key pair and extends validity, so
already-issued certificates keep chaining correctly.

`CaRenewalStatus` is `pending`, `success`, or `failed`.

Plan root renewal well before expiry. Everything the root signed becomes untrusted the moment it
lapses, and redistributing a new trust anchor across a fleet is slow work.

## CRL distribution

Infisical publishes Certificate Revocation Lists so clients can check whether a certificate has
been revoked.

Points to get right:

- Revoking a certificate in Infisical only takes effect for a client that actually **checks** the CRL. Many do not by default.
- The CRL distribution point must be reachable by every client that will validate certificates, including from outside your network if the certificates are used publicly.
- A CRL is only as fresh as its publication interval. There is a window after revocation in which a client with a cached CRL still trusts the certificate.

Short certificate lifetimes are a stronger control than revocation. Where you can automate renewal,
prefer short TTLs over relying on CRL checking.

## HSM connectors

An **HSM Connector** registers one slot on your Hardware Security Module so Infisical features can
perform PKCS#11 operations against it, including backing an Internal CA's key with the HSM.

The architecture matters:

- The Connector stores **credentials and routing only** — slot label and PIN, plus a Gateway reference. No key material.
- **Infisical never talks to the HSM directly.** A **Gateway** inside your network loads your HSM vendor's PKCS#11 driver and acts as the bridge.
- So an HSM connector always requires a working Gateway in the network where the HSM lives.

Fortanix DSM has a dedicated setup guide; other PKCS#11-compatible HSMs follow the generic path.

Use an HSM-backed key when the CA private key must never exist in software — typically a root CA
under a compliance regime that mandates hardware protection.
