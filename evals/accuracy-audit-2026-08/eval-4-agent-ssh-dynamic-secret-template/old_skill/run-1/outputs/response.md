Two things aren't in the skill's documented reference, so I'm flagging them rather than guessing silently:

1. **Field names on the SSH lease** — `template-functions.md` documents `dynamicSecret` return fields for SQL (`DB_USERNAME`/`DB_PASSWORD`), AWS IAM (`ACCESS_KEY`/`SECRET_ACCESS_KEY`/`SESSION_TOKEN`), and Redis, but not for SSH certificate leases. I've used `SSH_PRIVATE_KEY` and `SSH_CERTIFICATE` below by analogy with that naming pattern — verify against your actual lease object before relying on it (render once and inspect, or check the dashboard's lease preview).
2. **The `deploy` principal** — the `dynamicSecret` function signature is fixed at `project-slug, env, path, name, lease-ttl` with no principal/username argument. That means which principal the cert is signed for is controlled by how `prod-ssh` itself is configured in Infisical (allowed usernames on the dynamic secret), not by the template. Confirm `prod-ssh` is already scoped to `deploy` — if it allows multiple principals, this skill doesn't document a way to pick one at render time.

Also note: the agent config has no native file-permissions field for `destination-path`, so I'm using `execute.command` (documented for reload/restart hooks) to `chmod` the private key after render — SSH will refuse a world-readable key otherwise.

**templates/deploy_key.tpl**
```go
{{- with dynamicSecret "my-project" "prod" "/" "prod-ssh" "1h" }}
{{ .SSH_PRIVATE_KEY }}
{{- end }}
```

**templates/deploy_key-cert.tpl**
```go
{{- with dynamicSecret "my-project" "prod" "/" "prod-ssh" "1h" }}
{{ .SSH_CERTIFICATE }}
{{- end }}
```

Both pull from the same `dynamicSecret` call (same project/env/path/name/ttl), so per the skill's deduplication behavior they share a single lease rather than requesting two.

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
  type: "universal-auth"          # swap for a platform-native method (aws-iam, kubernetes, etc.) if applicable
  config:
    client-id: "./client-id"
    client-secret: "./client-secret"

sinks:
  - type: "file"
    config:
      path: "/tmp/access-token"

templates:
  - source-path: "./templates/deploy_key.tpl"
    destination-path: "/etc/ssh/deploy_key"
    config:
      polling-interval: "5m"
      execute:
        command: "chmod 600 /etc/ssh/deploy_key"
        timeout: 10

  - source-path: "./templates/deploy_key-cert.tpl"
    destination-path: "/etc/ssh/deploy_key-cert.pub"
    config:
      polling-interval: "5m"
      execute:
        command: "chmod 644 /etc/ssh/deploy_key-cert.pub"
        timeout: 10
```

`revoke-credentials-on-shutdown: true` is set since this is a leased SSH cert, so stopping the agent revokes the lease instead of leaving a signed cert live. Naming the private key and cert `deploy_key` / `deploy_key-cert.pub` follows OpenSSH's convention for auto-loading a cert alongside its key with `ssh -i /etc/ssh/deploy_key`.

If you tell me which platform this agent runs on (K8s, EC2, ECS, etc.), I can swap in the platform-native auth block instead of `universal-auth`.
