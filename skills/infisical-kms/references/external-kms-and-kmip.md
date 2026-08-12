# External KMS, KMIP, and Integrations

## External KMS

By default Infisical encrypts project data with its own KMS. You can instead root a project's
encryption in a cloud KMS you control, so the ultimate key custody sits with your cloud provider
rather than with Infisical.

Two providers: `aws` and `gcp`.

### AWS KMS

Credential types (`KmsAwsCredentialType`):

| Value | Meaning |
|-------|---------|
| `assume-role` | Infisical assumes an IAM role. **Preferred** |
| `access-key` | Static access key ID and secret |

For `assume-role`, the key field is `assumeRoleArn` — the role Infisical assumes. Also supply the
AWS region and the KMS key ID.

### GCP KMS

Credential type (`KmsGcpCredentialType`): `service_account`.

Note the value is `service_account` with an **underscore**, not `service-account`. The comment in
the source is explicit that this matches Google's own convention rather than Infisical's usual
hyphenated style.

Key fetch auth types (`KmsGcpKeyFetchAuthType`):

| Value | Meaning |
|-------|---------|
| `credential` | Resolve the key using the supplied credential |
| `kmsId` | Reference an existing configured KMS by ID |

Configuration fields include `gcpRegion` and `keyName` alongside the credential.

### When to use an external KMS

Use it when a compliance regime requires that key custody remain with your cloud provider, or when
an existing key hierarchy is already authoritative in AWS/GCP KMS.

Understand the tradeoff before recommending it: Infisical now depends on that external KMS being
reachable and healthy. If the external KMS is unavailable or its key is deleted or disabled, the
data encrypted under it cannot be decrypted. Guard the key with deletion protection and appropriate
IAM.

### HSM root key

Self-hosted instances can derive the KMS root key from a **Hardware Security Module** instead of
the `ROOT_ENCRYPTION_KEY` environment variable. See the self-hosting HSM integration guide, and
`infisical-self-host`.

This is a distinct concept from PKI **HSM Connectors**, which back a certificate authority's signing
key. Both use PKCS#11 and an HSM; they protect different keys.

## KMIP

**Enterprise-only.** Lets KMIP-compatible clients and security tools use Infisical KMS through the
standard Key Management Interoperability Protocol.

### Architecture

The important structural point: **Infisical does not expose a KMIP endpoint directly.** You run a
KMIP server yourself and it proxies to Infisical.

1. KMIP clients talk to **your** KMIP server
2. The KMIP server forwards requests to Infisical KMS
3. The KMIP server authenticates to Infisical with an enrollment-based access token

The server is deployed with the Infisical CLI:

```bash
infisical kmip start
```

You create a KMIP server entity in Infisical, then enroll the deployed server against it using a
one-time enrollment token or AWS authentication. This is the **same enrollment model as Gateways
and Relays** — see `infisical-gateway`.

### Supported operations

For **symmetric keys**:

`Create`, `Register`, `Locate`, `Get`, `Activate`, `Revoke`, `Destroy`, `Get Attributes`, `Query`

Note the scope: symmetric keys only. A client expecting KMIP asymmetric key operations is not
supported here.

### Version compatibility

KMIP **1.0 through 1.4**. Clients requiring KMIP 2.x are not supported.

### Network requirements

| Direction | Requirement |
|-----------|-------------|
| KMIP client → KMIP server | Reach the server on port **5696** (or your configured port). Firewalls must allow it, and DNS must resolve if using hostnames |
| KMIP server → Infisical | Outbound HTTPS. For self-hosted, to your custom domain |

**All connections from the KMIP server are outbound.** No inbound ports need opening on the
server's network for it to reach Infisical — the same property that makes Gateways deployable
inside restrictive networks.

There is also a Dell PowerEdge specific guide for iDRAC integration.

### KMIP server API

Management endpoints exist for KMIP servers: list, create, get, update, delete, login, revoke, and
generate-enrollment-token. Use `generate-enrollment-token` to enroll a newly deployed server.

## Kubernetes encryption at rest

Infisical KMS can back Kubernetes **encryption at rest** for etcd via the
[`k8-kms-plugin`](https://github.com/Infisical/k8-kms-plugin).

This makes Infisical the KMS provider in the Kubernetes `EncryptionConfiguration`, so Secret
objects in etcd are encrypted with a key Infisical holds rather than a key sitting on the control
plane host.

Availability caveat worth stating up front: if the KMS provider is unreachable the API server
cannot decrypt Secrets. Plan for Infisical availability accordingly, and understand this is a
different thing from syncing secrets *into* Kubernetes — for that see
`infisical-kubernetes-operator`.

## Sigstore cosign

Infisical KMS integrates with [Sigstore cosign](https://github.com/sigstore/cosign) through the
[`sigstore-kms-infisical`](https://github.com/Infisical/sigstore-kms-infisical) plugin, for signing
and verifying container images and artifacts with a key managed in Infisical.

Default algorithm: **RSA_4096**.

Use this when you want cosign's ecosystem — transparency log, OCI attachment, admission-controller
verification — with the signing key held in Infisical rather than in a file or a cloud KMS.

For signing build artifacts with approvals and a per-signer audit trail, consider PKI Code Signing
instead — see `infisical-pki`. Cosign integration is the right choice when the verification side is
already cosign-based.

## Choosing an integration

| The user wants... | Path |
|-------------------|------|
| Key custody in their own AWS/GCP account | External KMS |
| Key material in dedicated hardware | HSM root key (self-hosted) |
| A legacy tool that speaks KMIP to use Infisical keys | KMIP server |
| etcd Secrets encrypted with an Infisical key | `k8-kms-plugin` |
| Container image signing verified by cosign | `sigstore-kms-infisical` |
| Build artifacts signed with approvals and audit | PKI Code Signing (`infisical-pki`) |
