# Code Signing

Code Signing lets teams sign software artifacts — JARs, container images, Windows installers,
Android APKs, Linux packages, scripts — with a certificate whose **private key never leaves
Infisical**.

The signing model is remote: the tool sends a hash, Infisical signs it, the tool attaches the
resulting signature. No key material is exported at any point.

## Signers

A **Signer** is one signing identity. It bundles three things:

- A code-signing certificate issued by a CA (internal or external)
- The members allowed to use it
- An optional approval policy

One Signer per real signing concern: `mobile-app-prod`, `firmware-release`,
`ci-staging-builds`. Product Admins create Signers, attach the certificate, and assign members.
Teams then work inside their assigned Signers.

Roles on a Signer: **Administrator**, **Operator**, **Auditor**.

Each Signer keeps an activity trail of every signing operation — successful, failed, and denied.

Do not model one Signer for the whole company. The point of separate Signers is that a compromise
or misuse is scoped, and the audit trail tells you which release line was affected.

## Approvals

A Signer can require approval before a signature is produced, with per-approval limits on **count**
and **time**. So an approval can authorize, say, five signatures within the next hour rather than
granting open-ended access.

This is the control that makes remote signing meaningfully safer than a key on a build machine: a
compromised CI runner cannot mint unlimited signatures, because each batch needs a human.

Recommend approvals for anything that ships to customers. Skip them for internal staging builds
where the friction is not worth it.

## Three ways to sign

| Method | Use for |
|--------|---------|
| **PKCS#11 module** | Cross-platform tools: `jarsigner`, `osslsigncode`, `cosign`, `apksigner`, `openssl`, `gpg` |
| **Windows KSP** | Microsoft `signtool` for `.exe`, `.dll`, `.msi` |
| **Sign API** | Direct API calls, when you control the code |

### PKCS#11 module

A small native library exposing Infisical Signers to any tool implementing **PKCS#11 v2.40**. Tools
make their normal PKCS#11 calls; the module forwards them to Infisical and returns the signature.
No tool modification needed.

Library filenames by platform:

| Platform | File |
|----------|------|
| Linux x86_64 | `libinfisical-pkcs11.so` |
| Linux ARM64 | `libinfisical-pkcs11.so` |
| macOS x86_64 | `libinfisical-pkcs11.dylib` |
| macOS ARM64 | `libinfisical-pkcs11.dylib` |
| Windows x86_64 | `libinfisical-pkcs11.dll` |

Install:

```bash
# Linux
sudo cp libinfisical-pkcs11.so /usr/local/lib/
sudo chmod 755 /usr/local/lib/libinfisical-pkcs11.so

# macOS
sudo cp libinfisical-pkcs11.dylib /usr/local/lib/
sudo chmod 755 /usr/local/lib/libinfisical-pkcs11.dylib
```

Configuration lives at `/etc/infisical/pkcs11.conf` by default. Override the path with the
`INFISICAL_CONFIG` environment variable:

```bash
export INFISICAL_CONFIG=/path/to/your/pkcs11.conf
```

Point your signing tool at the library the way it normally takes a PKCS#11 module — for
`jarsigner` that is `-providerClass`/`-providerArg`, for `osslsigncode` it is the `-pkcs11module`
flag, and so on. The module is transparent to the tool.

### Windows KSP

The Infisical **Key Storage Provider** plugs into Windows **CNG** (Cryptography API: Next
Generation) so Microsoft's `signtool` can sign with a key held in Infisical.

What happens on a signature: `signtool` hands the provider a hash of the file, the provider sends
it to Infisical, Infisical signs and returns the signature, `signtool` attaches it. The private key
never leaves Infisical.

Two builds — **match the plugin to the `signtool` you run**, not to your OS:

| Build | File |
|-------|------|
| 64-bit | `infisical-ksp.dll` |
| 32-bit | `infisical-ksp-x86.dll` |

Most setups use 64-bit `signtool`. Mixing a 64-bit provider with a 32-bit `signtool` fails in a way
that does not obviously point at the mismatch.

Prerequisites:

1. A **Machine Identity** with **Universal Auth** enabled — the provider authenticates with its Client ID and Client Secret. See `infisical-setup`
2. `signtool`, from the Windows SDK

Download:

```powershell
Invoke-WebRequest `
  -Uri "https://github.com/Infisical/infisical-ksp/releases/latest/download/infisical-ksp.dll" `
  -OutFile "infisical-ksp.dll"
```

Then register the provider and sign as usual with `signtool`. The 32-bit path has an extra
registration note — check the doc when using `infisical-ksp-x86.dll`.

### Choosing between PKCS#11 and KSP

They are two front ends onto the same Signers. Pick by tool:

- Signing with `signtool` on Windows → **KSP**
- Signing with `jarsigner`, `cosign`, `osslsigncode`, `apksigner` → **PKCS#11**
- Signing from code you own → **Sign API** directly

There is no functional difference in what gets signed or how the key is protected.

## Certificates for code signing

A code-signing certificate needs the **code signing** extended key usage:

- Standard value: `code_signing`
- Legacy value: `codeSigning`
- OID: `1.3.6.1.5.5.7.3.3`

Key usage should include `digitalSignature`.

For artifacts distributed to the public, the certificate must chain to a publicly trusted CA — use
DigiCert, GoDaddy, or another public CA (see `references/certificate-authorities.md`). An internal
CA is fine for internal artifacts, and for anything where you control the trust store.

Windows in particular is strict: unsigned or untrusted-chain executables trigger SmartScreen
warnings regardless of whether the signature is cryptographically valid.

## Operational guidance

- **One Signer per release line.** Scope compromise and make the audit trail meaningful.
- **Approvals on anything customer-facing**, with tight count and time limits.
- **Machine identity per CI pipeline**, not one shared across all of them — so you can revoke a single pipeline's access.
- **Watch the activity trail.** Denied and failed signing attempts are a security signal worth alerting on.
- **Timestamp your signatures.** A timestamped signature remains valid after the signing certificate expires, which matters for software with a long shelf life. This is a function of your signing tool's timestamp flag, not of Infisical.
