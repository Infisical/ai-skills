# Infisical AI Skills

Give your AI coding agent accurate knowledge about [Infisical](https://infisical.com) — the open-source secret management platform.

## Recommended: Connect our Docs MCP

The fastest way to stop your AI from hallucinating about Infisical is to connect our docs MCP server. It works with any MCP-compatible agent, auto-updates when our docs change, and requires zero maintenance.

**URL:** `https://infisical.com/docs/mcp`

**Claude Code:**
```bash
claude mcp add --transport http infisical-docs https://infisical.com/docs/mcp
```

**Cursor / Windsurf:** Add to your MCP settings:
```json
{
  "mcpServers": {
    "infisical-docs": {
      "url": "https://infisical.com/docs/mcp"
    }
  }
}
```

**VS Code / Copilot:** Add to `.vscode/mcp.json`:
```json
{
  "servers": {
    "infisical-docs": {
      "url": "https://infisical.com/docs/mcp"
    }
  }
}
```

Any MCP-compatible client can connect with that URL.

## Alternative: Agent Skills

If your tool doesn't support MCP, or you want offline/local context, you can install these skills instead. They follow the [Agent Skills](https://agentskills.io) open standard and work across 45+ AI tools.

### Universal install

```bash
npx skills add Infisical/ai-skills
```

### Claude Code (plugin marketplace)

```bash
/plugin marketplace add Infisical/ai-skills
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

### infisical-terraform

Guide for the Infisical Terraform Provider. Covers:

- **Ephemeral resources** — Terraform 1.10+ secrets that never land in state files
- **Provider setup** — `infisical/infisical` source, Universal Auth and OIDC authentication
- **Data sources** — Traditional approach for older Terraform versions (with state storage caveats)
- **Project roles** — `permissions_v2` format with subject/action structure
- **Terraform Cloud** — OIDC integration for zero-credential CI/CD pipelines

### infisical-api

Guide for the Infisical REST API. Covers:

- **Authentication** — Universal Auth login, Bearer token usage, all machine identity auth methods
- **Secrets CRUD** — `/api/v4/secrets` endpoints (v1/v2/v3 are deprecated)
- **Projects & identities** — Project management, environments, members, groups, folders
- **Pagination** — `offset`/`limit` (default 20, max 100)
- **Rate limits** — Cloud-only limits by plan tier; self-hosted has no limits

### infisical-self-host

Guide for self-hosting Infisical. Covers:

- **Docker** — Standalone container and Docker Compose production stack
- **Kubernetes** — Helm chart from Cloudsmith registry, secrets, scaling, security
- **Environment variables** — `ENCRYPTION_KEY` (hex 16-byte), `AUTH_SECRET` (base64 32-byte), database, Redis
- **Scaling & HA** — Stateless horizontal scaling, PostgreSQL read replicas, Redis Sentinel
- **FIPS compliance** — FIPS 140-2 mode via separate image and `FIPS_ENABLED=true`

## Eval results

Every skill is A/B tested against a no-context baseline. We also ran a head-to-head comparison of Skills vs the Docs MCP. See [`evals/`](evals/) for full data.

### Skills vs no context

| Skill | With Skill | Without | Delta |
|-------|-----------|---------|-------|
| infisical-setup | 100% | 50% | **+50pp** |
| infisical-secret-syncs | 100% | 39% | **+61pp** |
| infisical-dynamic-secrets | 94% | 67% | **+28pp** |
| infisical-agent | 100% | 33% | **+67pp** |

### Skills vs MCP vs no context

| Test case | No context | MCP (best-case) | Skills |
|-----------|-----------|-----------------|--------|
| Python SDK | 0% | 100% | 100% |
| Node.js SDK | 33% | 100% | 100% |
| API endpoints | 38% | 100% | 100% |
| Terraform ephemeral | 13% | 100% | 100% |
| Self-hosted Docker | 38% | 88% | 100% |
| **Average** | **24%** | **98%** | **100%** |

Both approaches dramatically reduce hallucination. The MCP is recommended because it auto-updates with the docs and requires no maintenance.

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
