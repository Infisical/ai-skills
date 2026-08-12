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
- **SDKs** — Node.js, Python, Go, Java, .NET, Ruby, PHP, Rust, C++ (correct package names, imports, and class names)
- **Docker** — Build-time and runtime secret injection, `infisical run` entrypoint pattern
- **Kubernetes** — Operator installation, InfisicalSecret CRD, Kubernetes Auth setup
- **CI/CD** — GitHub Actions (OIDC Auth), GitLab CI (`id_tokens`)
- **Auth methods** — All 13 machine identity auth methods with a decision tree for choosing the right one

### infisical-secret-syncs

Guide for pushing secrets from Infisical to all 48 supported destinations. Covers:

- **Cloud** — AWS Secrets Manager, AWS Parameter Store, GCP Secret Manager, Azure Key Vault, Azure App Configuration, OCI Vault, HashiCorp Vault, 1Password
- **CI/CD** — GitHub (repo/org/repo-environment), GitLab, Bitbucket, CircleCI, Travis CI, TeamCity, Azure DevOps, Octopus Deploy, Spacelift, Terraform Cloud, Rundeck
- **Hosting/PaaS** — Vercel, Netlify, Cloudflare Workers/Pages, Railway, Render, Fly.io, Heroku, Northflank, DigitalOcean, Qovery, Cloud 66, Laravel Forge, OVH
- **Data** — Databricks, Snowflake, Supabase, Hasura Cloud
- **Configuration** — App Connections, key schemas, mapping behavior (AWS SM only), exact initial-sync enum values

### infisical-dynamic-secrets

Guide for on-demand, short-lived credentials across all 30 providers. Covers:

- **SQL databases** — PostgreSQL, MySQL, MSSQL, Oracle, SAP ASE/HANA, Snowflake, Vertica, ClickHouse, Azure SQL (custom creation statements)
- **NoSQL, cache & search** — Redis (ACL), AWS ElastiCache, AWS MemoryDB, MongoDB, MongoDB Atlas, Elasticsearch, Couchbase, RabbitMQ, Milvus
- **Cloud IAM** — AWS IAM Users, AWS STS, GCP service account impersonation, Azure Entra ID
- **Infrastructure & SaaS** — CA-signed SSH certificates, K8s service account tokens, LDAP, GitHub App tokens, Tailscale, IBM API Connect, TOTP
- **Lease lifecycle** — Generate, renew, and revoke with TTL management

### infisical-agent

Guide for the Infisical Agent client daemon. Covers:

- **Config format** — Full YAML reference with auth, sinks, and templates sections
- **Auth methods** — Universal Auth, Kubernetes, AWS IAM, Azure, GCP ID Token, GCP IAM
- **Template functions** — `listSecrets`, `listSecretsByProjectSlug`, `getSecretByName`, `dynamicSecret` (incl. the SSH-required `principals` argument)
- **Deployment patterns** — Docker Compose sidecar, AWS ECS sidecar, K8s init container, K8s sidecar
- **Advanced** — Polling intervals, on-change commands, exit-after-auth, caching

### infisical-terraform

Guide for the Infisical Terraform Provider. Covers:

- **Ephemeral resources** — Terraform 1.10+ secrets that never land in state files
- **Provider setup** — `infisical/infisical` source, nested `auth = { universal = {...} }` / `auth = { oidc = {...} }` blocks
- **Data sources** — Traditional approach for older Terraform versions (with state storage caveats)
- **Project roles** — `permissions_v2` format with subject/action structure
- **Terraform Cloud** — OIDC integration for zero-credential CI/CD pipelines

### infisical-api

Guide for the Infisical REST API. Covers:

- **Authentication** — Universal Auth login, Bearer token usage, all machine identity auth methods
- **Secrets CRUD** — `/api/v4/secrets` endpoints (v1/v2/v3 are deprecated)
- **Projects & identities** — Project management, environments, members, groups, folders
- **Pagination** — where it exists: `{ <resource>, totalCount }`. `/api/v4/secrets` is *not* paginated
- **Rate limits** — apply to self-hosted too (instance defaults 60 read / 200 write / 60 secrets per min); cloud limits vary by plan

### infisical-self-host

Guide for self-hosting Infisical. Covers:

- **Docker** — Standalone container and Docker Compose production stack
- **Kubernetes** — Helm chart from Cloudsmith registry, secrets, scaling, security
- **Environment variables** — `ENCRYPTION_KEY` (hex 16-byte, or base64 256-bit under FIPS), `AUTH_SECRET` (base64 32-byte), PostgreSQL, Redis
- **Scaling & HA** — Stateless horizontal scaling, PostgreSQL read replicas, Redis standalone/Sentinel/Cluster, required `noeviction` policy
- **FIPS compliance** — FIPS 140-3 via the separate `infisical/infisical-fips` image and `FIPS_ENABLED=true`

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

### Accuracy audit: stale skills are worse than no skill

The skills are periodically re-verified against the Infisical codebase. The most recent audit ran
a three-arm regression eval — no skill, pre-audit skill, post-audit skill — with tools disabled so
the model could not look anything up:

| Arm | Score | Pass rate |
|-----|-------|-----------|
| No skill | 18/35 | 51.4% |
| Pre-audit skill | 13/35 | **37.1%** |
| Post-audit skill | 35/35 | **100.0%** |

The pre-audit skills scored **below the no-skill baseline**. Outdated specifics don't merely fail
to help — they override correct model knowledge. On the secret-syncs case the base model scored
5/5 unaided and the stale skill pulled it down to 2/5.

This is the strongest argument for the MCP: it tracks the docs automatically, so it cannot drift
the way a vendored copy can. If you do install the skills, pin a version and re-pull when
Infisical ships new providers or auth methods. Full data and a reproducible harness live in
[`evals/accuracy-audit-2026-08/`](evals/accuracy-audit-2026-08/).

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
| `require 'infisical-sdk'` in Ruby | `require "infisical"` — gem name and require path differ |
| `InfisicalSDK::InfisicalClient.new(url)` | `Infisical::Client.new(site_url: url)` |
| Terraform `provider "infisical" { client_id = ... }` | Credentials nest inside `auth = { universal = {...} }` |
| Terraform `ephemeral "infisical_secret" { secret_key = ... }` | The attribute is `name`, not `secret_key` |
| `GET /api/v4/secrets?offset=0&limit=20` | That endpoint has no pagination; it returns everything at the path |
| Paginated responses return `{ items, total }` | They return `{ <resource>, totalCount }` |
| Self-hosted has no rate limits | Self-hosted has limits too (60 read / 200 write / 60 secrets per min by default) |
| GitHub sync scope `environment` | `repository-environment`; visibility is `all`/`private`/`selected` |
| `import-prioritize-infisical` | `import-prioritize-source` (values name source/destination, not the provider) |
| FIPS via `infisical/infisical:latest-fips` | FIPS 140-3 via the separate `infisical/infisical-fips` image |

These skills correct all of that.

## Contributing

To add a new skill:

1. Create a directory under `skills/` with a `SKILL.md` and optional `references/` folder
2. Create a matching plugin wrapper under `plugins/` with a `.claude-plugin/plugin.json`
3. Add a plugin entry in `.claude-plugin/marketplace.json`
4. Update `AGENTS.md` with the new skill
5. Run `claude plugin validate .` to check for errors
6. Add eval cases and run A/B benchmarks (see `evals/` for examples)

### Keeping skills accurate

Skill content is a vendored snapshot of a moving codebase, and the accuracy audit showed a
drifted skill performs *worse than no skill*. When re-verifying:

- **Cite the source, not the docs prose.** Counts and enum values come from the code:
  `secret-sync-enums.ts`, `dynamic-secret/providers/models.ts`, `db/schemas/models.ts`
  (`IdentityAuthMethod`), `server/routes/v4/`. Docs pages lag; enums don't.
- **Prefer exact literals over prose descriptions.** `repository-environment` beats "the
  environment scope". Wrong literals are the failure mode that hurts most.
- **Re-sync the plugin wrappers.** `plugins/<name>/skills/<name>/` is a copy of
  `skills/<name>/`; they drift silently. Diff them before committing.
- **Run the regression eval.** `evals/accuracy-audit-2026-08/run_evals.py` compares
  no-skill / old-skill / new-skill with tools disabled. Add assertions for whatever you just
  corrected so the next audit catches a regression.

## License

MIT
