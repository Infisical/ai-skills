# KMS Keys and Operations

All endpoints are under `/api/v1/kms`.

## Creating a key

```
POST /api/v1/kms/keys
```

| Field | Required | Description |
|-------|----------|-------------|
| `projectId` | Yes | The project the key belongs to |
| `name` | Yes | Key name, unique in the project |
| `keyUsage` | Yes | `encrypt-decrypt`, `sign-verify`, or `generate-verify-mac` |
| `encryptionAlgorithm` | For `encrypt-decrypt` | Symmetric algorithm |
| `algorithm` | For `sign-verify` / `generate-verify-mac` | Asymmetric or HMAC algorithm |
| `description` | No | |
| `isExportable` | No | Whether private key material may be exported. Defaults to false |

```bash
curl -X POST 'https://us.infisical.com/api/v1/kms/keys' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "<project-id>",
    "name": "app-data-key",
    "keyUsage": "encrypt-decrypt",
    "encryptionAlgorithm": "aes-256-gcm"
  }'
```

## Algorithm values

These differ in casing convention between subsystems. Copy them exactly.

### Symmetric — for `encrypt-decrypt`

| Algorithm | Value |
|-----------|-------|
| AES-256-GCM | `aes-256-gcm` |
| AES-128-GCM | `aes-128-gcm` |

**Lowercase, hyphenated.** Default to `aes-256-gcm`.

### Asymmetric key algorithms — for `sign-verify`

| Algorithm | Value |
|-----------|-------|
| RSA 4096 | `RSA_4096` |
| ECC NIST P-256 | `ECC_NIST_P256` |
| ECC NIST P-384 | `ECC_NIST_P384` |
| ECC NIST P-521 | `ECC_NIST_P521` |
| ML-DSA-44 (PQC) | `ML_DSA_44` |
| ML-DSA-65 (PQC) | `ML_DSA_65` |
| ML-DSA-87 (PQC) | `ML_DSA_87` |

**UPPER_SNAKE_CASE.** Note RSA 4096 is the only RSA size offered for KMS signing.

The ECC names here are `ECC_NIST_P256` style — **not** the `EC_prime256v1` form used by
`infisical-pki`. The two products name the same curve differently. Do not copy values between them.

Similarly PQC here is `ML_DSA_65` with **underscores**; PKI uses `ML-DSA-65` with **hyphens**.

### Signing algorithms — passed per sign/verify call

| Family | Values |
|--------|--------|
| RSASSA-PSS | `RSASSA_PSS_SHA_256`, `RSASSA_PSS_SHA_384`, `RSASSA_PSS_SHA_512` |
| RSASSA-PKCS1 v1.5 | `RSASSA_PKCS1_V1_5_SHA_256`, `RSASSA_PKCS1_V1_5_SHA_384`, `RSASSA_PKCS1_V1_5_SHA_512` |
| ECDSA | `ECDSA_SHA_256`, `ECDSA_SHA_384`, `ECDSA_SHA_512` |
| ML-DSA (PQC) | `ML_DSA_44`, `ML_DSA_65`, `ML_DSA_87` |

The signing algorithm must be compatible with the key's algorithm — an RSA key cannot use
`ECDSA_SHA_256`. For **ML-DSA the signing algorithm equals the key algorithm**; there is no hash
variant to choose.

Prefer RSASSA-PSS over PKCS1 v1.5 for new work; PKCS1 v1.5 exists for compatibility with systems
that require it.

To discover what a given key supports:

```
GET /api/v1/kms/keys/:keyId/signing-algorithms
```

### HMAC algorithms — for `generate-verify-mac`

| Algorithm | Value |
|-----------|-------|
| HMAC-SHA-1 | `HMAC_SHA_1` |
| HMAC-SHA-224 | `HMAC_SHA_224` |
| HMAC-SHA-256 | `HMAC_SHA_256` |
| HMAC-SHA-384 | `HMAC_SHA_384` |
| HMAC-SHA-512 | `HMAC_SHA_512` |

`HMAC_SHA_1` is available for legacy interoperability. Do not recommend it for new work.

## Encrypt and decrypt

Both plaintext and ciphertext are **base64-encoded**.

```bash
# Encrypt
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/encrypt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "plaintext": "'"$(echo -n 'my secret data' | base64)"'" }'
# -> { "ciphertext": "<base64>" }

# Decrypt
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/decrypt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "ciphertext": "<base64 ciphertext>" }'
# -> { "plaintext": "<base64>" }
```

The returned `plaintext` is base64 — decode it. A user reporting "decrypt returns garbage" has
almost always skipped the base64 decode.

| Endpoint | Method |
|----------|--------|
| `/keys/:keyId/encrypt` | POST |
| `/keys/:keyId/decrypt` | POST |

## Sign and verify

```bash
# Sign
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "<base64 data>",
    "signingAlgorithm": "RSASSA_PSS_SHA_256",
    "isDigest": false
  }'
# -> { "signature": "<base64>", "keyId": "...", "signingAlgorithm": "..." }

# Verify
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "<base64 data>",
    "signature": "<base64 signature>",
    "signingAlgorithm": "RSASSA_PSS_SHA_256",
    "isDigest": false
  }'
# -> { "signatureValid": true, "keyId": "...", "signingAlgorithm": "..." }
```

**`isDigest`** (default `false`) is the field people miss:

- `isDigest: false` — `data` is the raw message; Infisical hashes it, then signs
- `isDigest: true` — `data` is **already a hash**; Infisical signs it as-is

Use `isDigest: true` for large files: hash locally, send only the digest. Sending a pre-computed
digest with `isDigest: false` produces a signature over the hash-of-the-hash, which verifies
against nothing.

Verify returns `signatureValid` as a boolean. It does not error on an invalid signature — check the
field.

## HMAC

```bash
# Generate
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/generate-mac" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "data": "<base64 data>" }'
# -> { "mac": "<base64>", "keyId": "...", "macAlgorithm": "HMAC_SHA_256" }

# Verify
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/verify-mac" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "data": "<base64 data>", "mac": "<base64 mac>" }'
```

The MAC algorithm comes from the key, so it is not passed per call.

MAC versus signature: a MAC uses one shared key, so anyone who can verify can also forge. A
signature uses a private/public pair, so verifiers cannot forge. **Use `sign-verify` whenever a
third party needs to verify.** Use MAC only between parties that already share trust.

## Key management endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/keys` | POST | Create a key |
| `/keys` | GET | List keys |
| `/keys/:keyId` | GET | Get a key by ID |
| `/keys/key-name/:keyName` | GET | Get a key by name |
| `/keys/:keyId` | PATCH | Update a key |
| `/keys/:keyId` | DELETE | Delete a key |
| `/keys/:keyId/rotate` | POST | Rotate a key |
| `/keys/:keyId/public-key` | GET | Fetch the public key (asymmetric keys) |
| `/keys/:keyId/private-key` | GET | Fetch the private key — **exportable keys only** |
| `/keys/bulk-import` | POST | Import multiple keys |
| `/keys/bulk-export-private-keys` | POST | Export private keys — **exportable keys only** |
| `/keys/:keyId/signing-algorithms` | GET | Which signing algorithms this key supports |

### Rotation

```
POST /api/v1/kms/keys/:keyId/rotate
```

Rotation creates a new key version used for **subsequent** operations. It does **not** re-encrypt
data already encrypted under an older version — that ciphertext remains decryptable with the
version that produced it.

So rotation limits the blast radius of a future compromise going forward; it does not retroactively
protect existing ciphertext. If a user needs existing data re-protected, they must decrypt and
re-encrypt it themselves.

### Exportable keys

`isExportable` controls whether private key material can ever leave Infisical, via
`/keys/:keyId/private-key` or `/keys/bulk-export-private-keys`.

Default is non-exportable, and that is the stronger posture — the key genuinely cannot leak from
the platform. Only enable it for a real requirement, such as needing the same key in a system that
cannot call Infisical. Say plainly that it trades away the main guarantee.

The public key of an asymmetric key is always retrievable via `/keys/:keyId/public-key`; that is
not affected by `isExportable`.

## Envelope encryption

KMS calls are network round trips with request size limits, so do not push large payloads through
them. Standard pattern:

1. Generate a random data key locally
2. Encrypt the payload locally with the data key (AES-GCM)
3. Call KMS `encrypt` on the **data key** only
4. Store the encrypted data key alongside the ciphertext
5. To read: call KMS `decrypt` on the data key, then decrypt the payload locally

This keeps exactly one small KMS call per object regardless of payload size, and the plaintext data
key never persists.

## Root of trust

By default Infisical encrypts your data with its own KMS. Self-hosted instances derive the KMS root
key from the `ROOT_ENCRYPTION_KEY` environment variable, or from an **HSM**.

You can also back a project's encryption with an external KMS — see
`references/external-kms-and-kmip.md`.
