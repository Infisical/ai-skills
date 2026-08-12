Here's the approach, and the key idea that solves your network question.

## The core idea

RSA signing schemes (PKCS#1 v1.5 or PSS) never operate on raw file bytes directly. They sign a fixed-length hash of the data. So the actual cryptographic operation the KMS performs only ever needs a digest (32-64 bytes), not the file itself. That means for a large file, you should:

1. Hash the file locally, streaming it off disk so you never buffer the whole thing in memory.
2. Send only that digest to Infisical KMS's sign endpoint.
3. Get back a signature you can attach to the file.

This is the same pattern AWS KMS, GCP KMS, and PKCS#11 HSMs use for exactly this reason: shipping a multi-GB file to a signing service is wasteful and often not even supported for "raw message" signing (many services cap raw-message input at a few KB and require digest mode for anything larger).

## Step 1: Create an RSA signing key

Create an asymmetric KMS key in Infisical scoped for sign/verify (not encrypt/decrypt), e.g. RSA_4096 with a signing algorithm like `RSASSA_PKCS1_V1_5_SHA_256` or `RSASSA_PSS_SHA_256`.

## Step 2: Hash the file locally with a stream

```js
import { createHash } from "crypto";
import { createReadStream } from "fs";

function hashFile(path) {
  return new Promise((resolve, reject) => {
    const hash = createHash("sha256");
    const stream = createReadStream(path);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.on("end", () => resolve(hash.digest("base64")));
    stream.on("error", reject);
  });
}
```

This reads the file in chunks, so memory use stays flat regardless of file size, and nothing leaves your machine yet.

## Step 3: Sign the digest, not the file

```js
const digest = await hashFile("large-file.bin");

const res = await fetch(`${INFISICAL_API_URL}/api/v1/kms/keys/${keyId}/sign`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    signingAlgorithm: "RSASSA_PKCS1_V1_5_SHA_256",
    isDigest: true,
    data: digest,
  }),
});

const { signature } = await res.json();
```

Only the ~44 base64 characters of the SHA-256 digest cross the wire, regardless of whether the file is 10MB or 10GB.

## Step 4: Verify the same way

```js
const verifyRes = await fetch(`${INFISICAL_API_URL}/api/v1/kms/keys/${keyId}/verify`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    signingAlgorithm: "RSASSA_PKCS1_V1_5_SHA_256",
    isDigest: true,
    data: digest,
    signature,
  }),
});
```

Verification has the same property: whoever verifies just needs the digest and the signature, not the original file, as long as they trust the digest was computed correctly.

## One caveat

I don't have live web access in this session, so I can't pull the current Infisical API reference to confirm the exact field name for digest mode (I've represented it above as `isDigest`, matching the pattern used by AWS KMS's `MessageType: DIGEST`). Before you rely on this in code, check your instance's KMS API docs (or its OpenAPI spec if self-hosted) to confirm the parameter name and that your chosen algorithm supports digest input. The digest-then-sign strategy itself is standard practice and will hold regardless of the exact field name.
