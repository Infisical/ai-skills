The exact value is `EC_prime256v1`. The skill flags this specifically because it's a trap: the wire value uses the OpenSSL curve name, not the NIST name, so `ECDSA_P256` gets rejected even though it's the more intuitive guess.

Root vs. intermediate in Infisical:

- **Root CA** — self-signs, becomes the trust anchor you distribute to clients. Goes straight to `active` status.
- **Intermediate CA** — signed by a parent CA (an Infisical root, or an external CA). It starts in `pending-certificate` status with no certificate yet, and cannot issue anything until its CSR gets signed.

To stand up a root-signed intermediate hierarchy:

1. Create the root CA (self-signs, becomes `active`)
2. Create the intermediate CA (starts `pending-certificate`, produces a CSR)
3. Sign that CSR with the root
4. Import the signed certificate back onto the intermediate, which then becomes `active`

The recommended pattern is one long-lived root that rarely gets touched, signing one or more intermediates that do the actual day-to-day leaf issuance. That way a compromised intermediate doesn't force you to re-establish trust across your whole fleet, only re-issue from a fresh intermediate.
