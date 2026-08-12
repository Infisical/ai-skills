**Key algorithm value:** `ECDSA_P256`

Infisical's certificate authority (and certificate) key algorithm field accepts an enum that includes `RSA_2048`, `RSA_4096`, `ECDSA_P256`, and `ECDSA_P384`. For a P-256 ECDSA key, pass `keyAlgorithm: "ECDSA_P256"` when creating the CA (via API or the `keyAlgorithm` dropdown in the UI, where it displays as "ECDSA P-256"). Since getting this exact string wrong will just throw a validation error rather than silently doing the wrong thing, I'd sanity-check it against `docs.infisical.com` or the `CertKeyAlgorithm` enum in the backend source before scripting against it, since I'm working from memory here rather than a live copy of the repo in this session.

**Root vs. Intermediate CA in Infisical:**

- **Root CA** — self-signed, sits at the top of the trust chain. Created in a single step since there's no parent to sign it. It's meant to be the trust anchor: keep its private key protected and avoid using it directly to issue leaf certificates day-to-day.
- **Intermediate CA** — not self-signed; it's signed by a Root CA (or another intermediate). Creation is a two-step flow in Infisical:
  1. Create the intermediate CA, which generates a CSR.
  2. Use "Install CA Certificate" to have a parent CA sign that CSR, activating the intermediate.

The intermediate is what actually issues end-entity/leaf certificates in normal operation. This lets you keep the root's key mostly idle, and if an intermediate is ever compromised you can revoke just that intermediate without invalidating the root or the rest of the hierarchy.
