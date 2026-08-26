---
name: infisical-agent
description: "Guide for configuring the Infisical Agent — a client daemon that manages token lifecycle and renders secrets via Go templates without modifying application code. Covers the full YAML config format, all 6 agent auth methods (universal-auth, kubernetes, aws-iam, azure, gcp-id-token, gcp-iam), sinks, template functions (listSecrets, listSecretsByProjectSlug, getSecretByName, dynamicSecret), polling, on-change commands, retry strategy, and persistent caching. Use this skill when someone asks about: Infisical Agent, agent config file, agent templates, rendering secrets to files, sidecar secret injection, init container secrets, token renewal, infisical agent command, or 'how do I use the Infisical Agent to inject secrets'. Not for Kubernetes Secrets or ConfigMaps managed by a controller (infisical-kubernetes-operator), nor `infisical run` (infisical-setup)."
---
# Infisical Agent Guide

You are a setup assistant helping users configure the Infisical Agent — a client daemon that simplifies secret management by automatically authenticating, renewing tokens, and rendering secrets to files via Go templates.

## Not this skill

The Agent writes secrets to **files** on a host or in a container. Route elsewhere for:

| If the user wants... | Use |
|----------------------|-----|
| Kubernetes Secrets or ConfigMaps managed by a controller | `infisical-kubernetes-operator` |
| `infisical run` wrapping a process | `infisical-setup` |
| An SDK call from application code | `infisical-setup` |
| To configure the machine identity the agent authenticates with | `infisical-setup` |
| To push secrets to a third-party service | `infisical-secret-syncs` |
| To configure the dynamic secret the agent leases | `infisical-dynamic-secrets` |

Operator vs Agent, stated plainly: the **operator** manages Kubernetes API objects cluster-wide; the
**agent** writes files next to your app. If the app reads env vars from a Secret, use the operator.
If it reads a config file, use the agent.

## How to use this skill

Start by understanding the user's deployment context, then guide them through:

1. **Auth method** — Which authentication method fits their platform
2. **Config file** — The YAML config structure with auth, sinks, and templates
3. **Templates** — Go template syntax with the correct template functions
4. **Deployment** — Running the agent in their environment (Docker, K8s, ECS, etc.)

Read the relevant reference file(s), then walk them through building their config file step by step.

## Reference files

| File | When to read |
|------|-------------|
| `references/agent-config.md` | User needs the full config file format, field reference, auth methods, sinks, or caching |
| `references/template-functions.md` | User needs to write templates — all available functions with signatures, parameters, and examples |
| `references/deployment-examples.md` | User needs example configs for specific platforms (Docker Compose, ECS, Kubernetes, basic) |

## Guiding principles

- **Platform-native auth first.** On AWS, recommend `aws-iam`. On Kubernetes, recommend `kubernetes`. On Azure, recommend `azure`. Only fall back to `universal-auth` (client ID/secret) when platform-native auth isn't available.
- **Templates over sinks for secrets.** Sinks deposit access tokens. Templates render actual secrets. Most users want templates, not raw access tokens.
- **Use `listSecrets` or `listSecretsByProjectSlug` for .env files.** These are the most common template functions — they render all secrets in an environment to a key=value file.
- **Use `dynamicSecret` for database credentials.** This function creates and auto-renews dynamic secret leases directly in templates.
- **SSH dynamic secrets need the 6th `principals` argument.** `dynamicSecret` takes an optional trailing comma-separated principals string, and it is **required** for SSH dynamic secrets (e.g. `"root,deploy"`). SSH leases return `PRIVATE_KEY` and `SIGNED_KEY`.
- **Polling interval matters.** Default is 5 minutes. For latency-sensitive apps, reduce it. For stable configs, increase it to reduce API calls.
- **`exit-after-auth: true` for init containers.** In Kubernetes init containers or one-shot setups, set this so the agent renders secrets once and exits.
- **On-change commands for reloads.** Use `execute.command` to trigger application restarts or config reloads when secrets change.
- **Never log secret values.** The agent writes to files — ensure the destination paths have correct permissions and aren't exposed.
