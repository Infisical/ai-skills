# Infisical AI Skills

Official [Agent Skills](https://agentskills.io) for [Infisical](https://infisical.com) — the open-source secret management platform.

These skills give AI coding agents accurate, up-to-date knowledge about Infisical's platform — SDKs, CLI, secret syncs, dynamic secrets, the Infisical Agent, Docker, Kubernetes, CI/CD, and auth methods. Without them, AI tools frequently hallucinate wrong package names, deprecated auth patterns, incorrect function signatures, and broken configurations.

## Install

### Universal (45+ agents)

Works with Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Windsurf, Gemini CLI, and more:

```bash
npx skills add Infisical/ai-skills
```

### Claude Code (plugin marketplace)

```bash
/plugin marketplace add Infisical/ai-skills
/plugin install infisical-setup@infisical-ai-skills
/plugin install infisical-secret-syncs@infisical-ai-skills
/plugin install infisical-dynamic-secrets@infisical-ai-skills
/plugin install infisical-agent@infisical-ai-skills
```

### Manual

Copy skill folders from `skills/` into your project's agent skills directory:

| Agent | Location |
|-------|----------|
| Claude Code | `.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Cursor | `.cursor/skills/` or `.agents/skills/` |
| GitHub Copilot | `.github/skills/` |

## What's included

### infisical-setup

Interactive setup guide for integrating Infisical into your projects. Covers:

- **CLI** — `infisical run`, `infisical init`, local development workflow
- **SDKs** — Node.js, Python, Go, Java, .NET, Ruby (correct package names, imports, and class names)
- **Docker** — Build-time and runtime secret injection, `infisical run` entrypoint pattern
- **Kubernetes** — Operator installation, InfisicalSecret CRD, Kubernetes Auth setup
- **CI/CD** — GitHub Actions (OIDC Auth), GitLab CI (`id_tokens`)
- **Auth methods** — All 12 machine identity auth methods with a decision tree for choosing the right one

### infisical-secret-syncs

Guide for pushing secrets from Infisical to 38+ third-party services. Covers:

- **Cloud** — AWS Secrets Manager, GCP Secret Manager, Azure Key Vault
- **DevOps** — GitHub (org/repo/env), Vercel, Cloudflare Workers, GitLab, Bitbucket
- **Infrastructure** — HashiCorp Vault, AWS Parameter Store, Terraform Cloud
- **Platforms** — Railway, Render, Fly.io, Heroku, Netlify, Supabase, and more
- **Configuration** — App Connections, key schemas, mapping behavior, initial sync options

### infisical-dynamic-secrets

Guide for on-demand, short-lived credentials across 27 providers. Covers:

- **SQL databases** — PostgreSQL, MySQL, MSSQL, Oracle, Cassandra, Snowflake (custom creation statements)
- **NoSQL & cache** — Redis (ACL), MongoDB, MongoDB Atlas, Elasticsearch, RabbitMQ
- **Cloud IAM** — AWS IAM Users, AWS STS, GCP service account impersonation
- **SSH & Kubernetes** — CA-signed SSH certificates, K8s service account tokens
- **Lease lifecycle** — Generate, renew, and revoke with TTL management

### infisical-agent

Guide for the Infisical Agent client daemon. Covers:

- **Config format** — Full YAML reference with auth, sinks, and templates sections
- **Auth methods** — Universal Auth, Kubernetes, AWS IAM, Azure, GCP ID Token, GCP IAM
- **Template functions** — `listSecrets`, `listSecretsByProjectSlug`, `getSecretByName`, `dynamicSecret`
- **Deployment patterns** — Docker Compose sidecar, AWS ECS sidecar, K8s init container, K8s sidecar
- **Advanced** — Polling intervals, on-change commands, exit-after-auth, caching

## Eval results

Every skill is A/B tested to prove it actually reduces hallucination. See [`evals/`](evals/) for full data.

| Skill | With Skill | Without Skill | Delta |
|-------|-----------|--------------|-------|
| infisical-setup | 100% | 50% | **+50pp** |
| infisical-secret-syncs | 100% | 39% | **+61pp** |
| infisical-dynamic-secrets | 94% | 67% | **+28pp** |
| infisical-agent | 100% | 33% | **+67pp** |
| **Overall** | **98%** | **46%** | **+52pp** |

## Why this exists

AI coding agents frequently get Infisical details wrong:

| What AI says | What's correct |
|-------------|---------------|
| `pip install infisical-python` | `pip install infisicalsdk` |
| `from infisical_client import InfisicalClient` | `from infisical_sdk import InfisicalSDKClient` |
| Use Service Tokens for Docker | Use machine identities (Service Tokens are deprecated) |
| `npm install -g infisical` | Install via `apt` from `artifacts-cli.infisical.com` |
| API Key Auth for Kubernetes | Kubernetes Auth (API Keys are deprecated) |
| GitHub syncs support importing | GitHub only supports overwrite (no import) |
| `listSecrets(projectId, env, path)` | `listSecrets` returns objects with `.Key`, `.Value`, `.SecretPath` fields |
| Agent uses JSON config | Agent uses YAML config with `infisical:` root key |

These skills correct all of that.

## Contributing

To add a new skill:

1. Create a directory under `skills/` with a `SKILL.md` and optional `references/` folder
2. Create a matching plugin wrapper under `plugins/` with a `.claude-plugin/plugin.json`
3. Add a plugin entry in `.claude-plugin/marketplace.json`
4. Update `AGENTS.md` with the new skill
5. Run `claude plugin validate .` to check for errors
6. Add eval cases and run A/B benchmarks (see `evals/` for examples)

## License

MIT
