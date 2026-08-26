Here's how to sign a large file with an RSA key in Infisical KMS while keeping the file itself off the network entirely.

## 1. Create a `sign-verify` RSA key

```bash
curl -X POST 'https://us.infisical.com/api/v1/kms/keys' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "<project-id>",
    "name": "file-signing-key",
    "keyUsage": "sign-verify",
    "algorithm": "RSA_4096"
  }'
```

This returns a `keyId` you'll use below.

## 2. Hash the file locally instead of sending it

This is the part that avoids the network transfer. Infisical's `sign` endpoint has an `isDigest` flag: when `true`, you send only a hash of the file, not the file itself, and Infisical signs that hash directly.

```bash
KEY_ID="<key-id-from-step-1>"

# Hash the file locally with SHA-256
DIGEST_B64=$(openssl dgst -sha256 -binary large-file.bin | base64)
```

The hash algorithm you pick here must match the signing algorithm's hash in the next step. SHA-256 pairs with `RSASSA_PSS_SHA_256`.

## 3. Sign the digest, not the file

```bash
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "'"$DIGEST_B64"'",
    "signingAlgorithm": "RSASSA_PSS_SHA_256",
    "isDigest": true
  }'
# -> { "signature": "<base64>", "keyId": "...", "signingAlgorithm": "RSASSA_PSS_SHA_256" }
```

Only the small digest crosses the wire, regardless of whether the file is 1 MB or 100 GB.

RSASSA-PSS is preferred over PKCS1 v1.5 for new work, so stick with `RSASSA_PSS_SHA_256` unless something you're interoperating with specifically requires PKCS1 v1.5.

## 4. Verify the same way

```bash
curl -X POST "https://us.infisical.com/api/v1/kms/keys/$KEY_ID/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "'"$DIGEST_B64"'",
    "signature": "<base64 signature from step 3>",
    "signingAlgorithm": "RSASSA_PSS_SHA_256",
    "isDigest": true
  }'
# -> { "signatureValid": true, ... }
```

Recompute the digest from the file on the verifying side the same way (`openssl dgst -sha256`), and check `signatureValid` is `true`. Verify never errors on a bad signature, it just returns `false`.

## The pitfall to avoid

Getting `isDigest` wrong is the most common mistake here:

- If you set `isDigest: false` (the default) but send a pre-computed hash as `data`, Infisical will hash your hash and sign that. The signature will verify against nothing meaningful.
- `isDigest: true` must be set consistently on both `sign` and `verify` calls, and the local hash algorithm must match the signing algorithm's hash suffix (`_SHA_256`, `_SHA_384`, etc.).

Everything else stays as normal base64-in, base64-out.
