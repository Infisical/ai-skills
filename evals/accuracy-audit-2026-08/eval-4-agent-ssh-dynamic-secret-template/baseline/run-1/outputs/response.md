Here's the Infisical Agent setup for that flow. Two pieces: the agent config (`config.yaml`) and the render template (`prod-ssh.tmpl`).

**config.yaml**
```yaml
infisical:
  address: "https://app.infisical.com"   # or your self-hosted URL

auth:
  type: "universal-auth"
  config:
    client-id: "<MACHINE_IDENTITY_CLIENT_ID>"
    client-secret: "<MACHINE_IDENTITY_CLIENT_SECRET>"
  remove_client_secret_on_read: false

sinks:
  - type: "file"
    config:
      path: "/etc/infisical/agent-token"

templates:
  - source-path: "/etc/infisical/templates/prod-ssh.tmpl"
    destination-path: "/etc/ssh/deploy_bundle"
    config:
      polling-interval: "30m"
      execute-command: "/etc/infisical/split-ssh-bundle.sh"
```

**prod-ssh.tmpl**
```gotemplate
{{- with dynamicSecret "prod-ssh" "prod" "/" "1h" "deploy" }}
###PRIVATE_KEY###
{{ .PrivateKey }}
###CERTIFICATE###
{{ .Certificate }}
###PUBLIC_KEY###
{{ .PublicKey }}
{{- end }}
```

The private key and the certificate must come from the same lease (the cert only validates against its matching key), so I'm rendering both to one file and splitting on `execute-command` rather than declaring two separate `templates:` entries, which would each pull an independent, mismatched lease.

**split-ssh-bundle.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail

BUNDLE="/etc/ssh/deploy_bundle"
KEY="/etc/ssh/deploy_id"
CERT="/etc/ssh/deploy_id-cert.pub"
PUB="/etc/ssh/deploy_id.pub"

awk -v key="$KEY" -v cert="$CERT" -v pub="$PUB" '
  /^###PRIVATE_KEY###$/ { f=key; next }
  /^###CERTIFICATE###$/ { f=cert; next }
  /^###PUBLIC_KEY###$/  { f=pub; next }
  f { print > f }
' "$BUNDLE"

chmod 600 "$KEY"
chmod 644 "$CERT" "$PUB"
rm -f "$BUNDLE"
```

With this layout, `ssh -i /etc/ssh/deploy_id deploy@<host>` works with no extra flags. OpenSSH auto-loads the sibling cert whenever it's named `<identity_file>-cert.pub`.

Two things worth double-checking on your end before you deploy this, since I don't have live doc access in this session to pin them against the exact current agent build:

1. The `dynamicSecret` function name/arg order above (`name, env, secretPath, ttl, principal`) is my best reconstruction, not a verified copy from current docs. Confirm it against `infisical-agent`'s own docs or `--help` for the version you're running.
2. Whether `deploy` needs to be passed at request time at all, or whether it's already locked in as the (sole) allowed principal on the `prod-ssh` dynamic secret's provider config, in which case you can drop that last template argument.

Given you're at Infisical, you're probably faster at confirming those two specifics than I am right now. Let me know if you want me to adjust once you've checked, or if you'd rather I dig through the actual docs source somewhere I do have fetch access.
