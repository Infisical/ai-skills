I don't have web or file-system tools available in this session (no WebFetch/Bash/Read), so I can't pull the live Infisical docs to verify exact current values before answering. Given this is a compliance-sensitive deployment (wrong image or key format could mean a non-compliant install), I'll give you what I know with confidence levels flagged rather than assert specifics I can't check right now. Please cross-check the flagged items against the FIPS section of infisical.com/docs before you deploy.

**Docker image (medium confidence)**
Infisical ships a separate FIPS-hardened image distinct from the standard `infisical/infisical` image, built against a FIPS-validated crypto module rather than the standard runtime. I recall the tag pattern as something like `infisical/infisical-fips:latest-postgres`. Confirm the exact repo/tag on Docker Hub or in the self-hosting docs before pulling, since tag naming conventions get revised.

**FIPS standard (medium confidence)**
My recollection is FIPS 140-2, based on running against a FIPS-validated OpenSSL module rather than Infisical's default crypto path (which uses libsodium/XSalsa20-Poly1305, an algorithm not on the FIPS-approved list). The FIPS build should force all envelope/data encryption onto FIPS-approved primitives (AES-256-GCM) instead. Verify the exact standard and revision (140-2 vs 140-3) and whether there's a validation certificate number cited, since that's the kind of claim you don't want to restate incorrectly.

**Environment variables (low to medium confidence on the FIPS-specific ones)**
Standard self-host variables you'll need regardless of FIPS mode:
- `DB_CONNECTION_URI` (Postgres)
- `REDIS_URL`
- `AUTH_SECRET` (JWT signing secret)
- `SITE_URL`
- The encryption key variable (see below)

For FIPS mode specifically, I'd expect a flag that forces the app onto the FIPS-approved crypto path (something like `FIPS_ENABLED=true`), on top of running the FIPS image itself. I'm not confident enough in the exact variable name to hand it to you as fact. Check the FIPS self-hosting page for the definitive list.

**Encryption key generation (medium confidence, and this is the one to get right)**
Infisical's newer architecture uses a root encryption key for its internal KMS, set via `ROOT_ENCRYPTION_KEY`, generated as:

```
openssl rand -base64 32
```

That's a 256-bit key, base64-encoded, and it feeds an AES-256-GCM path, which is why I'd expect FIPS mode to require this newer key variable rather than the legacy `ENCRYPTION_KEY` (32-char hex, used with libsodium secretbox, non-FIPS-approved algorithm). If your deployment is on an older version that predates the internal KMS migration, confirm whether `ENCRYPTION_KEY` or `ROOT_ENCRYPTION_KEY` is the one that governs the FIPS-approved path in that version.

**Bottom line:** the FIPS image and the AES-256-GCM/`ROOT_ENCRYPTION_KEY` path are the pieces I'd bet on, but the exact image tag, the FIPS revision number, and the FIPS-mode env var name need a check against current docs since I can't fetch them live here. If you paste the relevant doc page content, I can verify these against it directly.
