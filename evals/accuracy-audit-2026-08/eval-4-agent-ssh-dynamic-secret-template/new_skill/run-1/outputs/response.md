Here's the Infisical Agent config and templates for the `prod-ssh` dynamic secret, logging in as the `deploy` principal.

**agent-config.yaml**

```yaml
infisical:
  address: "https://app.infisical.com"
  exit-after-auth: false
  revoke-credentials-on-shutdown: true
  retry-strategy:
    max-retries: 3
    max-delay: "5s"
    base-delay: "200ms"

auth:
  type: "universal-auth"
  config:
    client-id: "./client-id"
    client-secret: "./client-secret"

templates:
  - source-path: "./templates/ssh-private-key.tpl"
    destination-path: "/etc/ssh/agent/id_rsa"
    config:
      polling-interval: "30m"
      execute:
        command: "chmod 600 /etc/ssh/agent/id_rsa"
        timeout: 10

  - source-path: "./templates/ssh-signed-cert.tpl"
    destination-path: "/etc/ssh/agent/id_rsa-cert.pub"
    config:
      polling-interval: "30m"
```

**templates/ssh-private-key.tpl**

```go
{{- with dynamicSecret "my-project" "prod" "/" "prod-ssh" "1h" "deploy" }}
{{ .PRIVATE_KEY }}
{{- end }}
```

**templates/ssh-signed-cert.tpl**

```go
{{- with dynamicSecret "my-project" "prod" "/" "prod-ssh" "1h" "deploy" }}
{{ .SIGNED_KEY }}
{{- end }}
```

Notes on why it's structured this way:

- The `dynamicSecret` call is identical in both templates (same project, env, path, secret name, TTL, and principal), so the agent dedupes it into a single lease and writes that one lease to both destination paths, rather than creating two separate leases.
- The private key and cert are split into two files named `id_rsa` and `id_rsa-cert.pub`. OpenSSH auto-discovers a certificate if it's named `<keyfile>-cert.pub` alongside the matching private key, so this pairing lets `ssh` pick both up without extra `-i`/`-o CertificateFile` flags.
- `"deploy"` is passed as the 6th argument since it's required for SSH dynamic secrets and must be in that dynamic secret's allowed-principals list in Infisical.
- The `execute.command` on the private key template re-applies `chmod 600` after every render, since SSH refuses to use a private key with overly permissive file permissions.
- `revoke-credentials-on-shutdown: true` ensures the lease is revoked when the agent stops rather than lingering.
- I used `universal-auth` as a placeholder since no platform was specified. Swap to `kubernetes`, `aws-iam`, `azure`, `gcp-id-token`, or `gcp-iam` if this runs on one of those platforms.
