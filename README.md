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

**17 skills** across the whole Infisical platform. Each declares what it is *not*, so an agent lands
on the right one — see [`AGENTS.md`](AGENTS.md) for the router and disambiguation table.

### Secrets delivery

| Skill | Covers |
|-------|--------|
| **infisical-setup** | CLI, all 9 SDKs (Node.js, Python, Go, Java, .NET, Ruby, PHP, Rust, C++), Docker, CI/CD, all 13 machine identity auth methods |
| **infisical-api** | `/api/v4/secrets` CRUD and batch, projects, identities, which endpoints paginate, rate limits |
| **infisical-terraform** | The provider's nested `auth` block, ephemeral resources, project roles, TFC OIDC |
| **infisical-agent** | Agent YAML config, Go template functions, sinks, polling, on-change commands |
| **infisical-kubernetes-operator** | v1beta1 CRDs and legacy v1alpha1, Helm install, `auto-reload`, push secrets |

### Moving and generating credentials

| Skill | Covers |
|-------|--------|
| **infisical-app-connections** | All 83 connection types, auth methods, and credential fields (generated from source). The shared prerequisite for syncs, rotations, PKI, and scanning |
| **infisical-secret-syncs** | Pushing secrets to all 48 destinations, key schemas, initial-sync enums |
| **infisical-dynamic-secrets** | On-demand short-lived credentials across all 30 providers, leases, SSH certificates |
| **infisical-secret-rotation** | Rotating existing credentials across 28 providers, dual-phase vs single-phase, the two-user SQL pattern |

### Other products

| Skill | Covers |
|-------|--------|
| **infisical-pki** | 9 CA types, Policies/Profiles/Applications, API/ACME/EST/SCEP enrollment, 12 PKI Syncs, code signing, HSM, post-quantum |
| **infisical-kms** | Encrypt/decrypt, sign/verify, HMAC, key rotation, external KMS, KMIP, cosign |
| **infisical-pam** | Brokered access to 13 account types for humans and AI agents, session recording, JIT approvals |
| **infisical-secret-scanning** | GitHub/GitLab/Bitbucket data sources, `infisical scan` CLI, pre-commit hooks, honey tokens |

### Platform and governance

| Skill | Covers |
|-------|--------|
| **infisical-access-control** | Roles, custom permissions, the granular secret actions, ABAC, temporary access, approvals, audit streams |
| **infisical-sso** | SAML/OIDC/LDAP and free Google/GitHub SSO, SCIM, group-to-role mapping, enforcement and break-glass |
| **infisical-gateway** | Private-network access with outbound-only tunnels, exact ports, Gateway Pools |
| **infisical-self-host** | Docker, Compose, Helm, env vars, Redis `noeviction`, FIPS 140-3, scaling and HA |

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

### New skills

The 10 skills added in the 7 → 17 expansion, A/B tested the same way:

| Arm | Score | Pass rate |
|-----|-------|-----------|
| No skill | 27/56 | 48.2% |
| With new skill | 56/56 | **100.0%** |

Null results are recorded, not hidden: on App Connections the base model already scored 4/4 unaided.
The skills matter most where the model has little knowledge — PAM and SSO scored 1/5 unaided, and the
Kubernetes Operator **0/5**, because unaided it reaches for the legacy `v1alpha1 InfisicalSecret` CRD
instead of current `v1beta1`. See [`evals/new-skills-2026-08/`](evals/new-skills-2026-08/).

### Generated reference files

The App Connection facts — 83 connections × auth methods × credential fields, and all 94 API
endpoints — are **generated from the Infisical source**, not hand-maintained:

```bash
python3 tools/generate-app-connection-refs.py          # regenerate
python3 tools/generate-app-connection-refs.py --check  # CI: fail on drift
```

This is the structural answer to the drift problem above. Facts are derived; only guidance is
written by hand. Re-verification is `regenerate && git diff`.

### Routing: does the right skill get picked?

With 17 skills, mis-routing becomes the dominant failure mode — a skill loaded for the wrong question
answers confidently from the wrong frame. So every skill declares what it is *not*, and
[`AGENTS.md`](AGENTS.md) carries a router plus a disambiguation table for the pairs that get confused.

Measured on 14 prompts sitting deliberately on a seam between two similar skills:

| Arm | Correct | Accuracy |
|-----|---------|----------|
| Skill descriptions only | 14/14 | **100.0%** |
| With router + boundaries | 14/14 | **100.0%** |

Getting there took two passes. Initially descriptions alone scored 13/14 — asked about short-lived
SSH certificates it chose `infisical-pam`, plausible but wrong, since SSH certificates come from
**SSH dynamic secrets**. The fix was moving the boundaries into the `description` frontmatter, because
that is what actually decides whether a skill loads. See
[`evals/routing-2026-08/`](evals/routing-2026-08/).

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
| Kubernetes Operator uses `InfisicalSecret` | Current CRDs are `v1beta1`: `InfisicalConnection`, `InfisicalAuth`, `InfisicalStaticSecret` |
| A synced Kubernetes Secret restarts pods | It does not — add `secrets.infisical.com/auto-reload: "true"` to the workload |
| SQL rotation rotates one user's password | It alternates between **two** pre-existing users, `username1` and `username2` |
| ECDSA P-256 in PKI is `ECDSA_P256` | The wire value is `EC_prime256v1` |
| GitHub secret scanning uses a `github` connection | It requires a **`github-radar`** connection |
| SSH certificates come from the PKI product | They come from **SSH dynamic secrets** |
| Reaching a private database requires self-hosting | It requires a **Gateway**; Infisical Cloud works fine |
| Any App Connection can use a Gateway | Only 16 of the 83 types accept `gatewayId` |

These skills correct all of that.

## Contributing

To add a new skill:

1. Create a directory under `skills/` with a `SKILL.md` and optional `references/` folder
2. Create a matching plugin wrapper under `plugins/` with a `.claude-plugin/plugin.json`
3. Add a plugin entry in `.claude-plugin/marketplace.json`
4. Update `AGENTS.md` — add it to the router table, and add a row to the disambiguation table if it
   sits near an existing skill
5. Put the boundary in **two** places: a short "not for X (other-skill)" clause at the end of the
   `description` frontmatter — that is what decides whether the skill loads — and a `## Not this
   skill` section in the body, with reciprocal rows on the neighbours it could be confused with
6. Run `claude plugin validate .` to check for errors
7. Add eval cases and run A/B benchmarks (see `evals/` for examples)

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
