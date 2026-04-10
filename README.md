# Infisical AI Skills

Official [Agent Skills](https://agentskills.io) for [Infisical](https://infisical.com) — the open-source secret management platform.

These skills give AI coding agents accurate, up-to-date knowledge about Infisical's SDKs, CLI, Docker integration, Kubernetes Operator, CI/CD setup, and machine identity auth methods. Without them, AI tools frequently hallucinate wrong package names, deprecated auth patterns, and broken install commands.

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
```

### Manual

Copy `skills/infisical-setup/` into your project's agent skills directory:

| Agent | Location |
|-------|----------|
| Claude Code | `.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Cursor | `.cursor/skills/` or `.agents/skills/` |
| GitHub Copilot | `.github/skills/` |

## What's included

### infisical-setup

An interactive setup guide that helps you integrate Infisical into your projects. Covers:

- **CLI** — `infisical run`, `infisical init`, local development workflow
- **SDKs** — Node.js, Python, Go, Java, .NET, Ruby (correct package names, imports, and class names)
- **Docker** — Build-time and runtime secret injection, `infisical run` entrypoint pattern
- **Kubernetes** — Operator installation, InfisicalSecret CRD, Kubernetes Auth setup
- **CI/CD** — GitHub Actions (OIDC Auth), GitLab CI (`id_tokens`)
- **Auth methods** — All 12 machine identity auth methods with a decision tree for choosing the right one

## Why this exists

AI coding agents frequently get Infisical details wrong:

| What AI says | What's correct |
|-------------|---------------|
| `pip install infisical-python` | `pip install infisicalsdk` |
| `from infisical_client import InfisicalClient` | `from infisical_sdk import InfisicalSDKClient` |
| Use Service Tokens for Docker | Use machine identities (Service Tokens are deprecated) |
| `npm install -g infisical` | Install via `apt` from `artifacts-cli.infisical.com` |
| API Key Auth for Kubernetes | Kubernetes Auth (API Keys are deprecated) |

These skills correct all of that.

## Contributing

To add a new skill:

1. Create a directory under `skills/` and `plugins/infisical-setup/skills/` with a `SKILL.md`
2. Add a plugin entry in `.claude-plugin/marketplace.json`
3. Update `AGENTS.md`
4. Run `claude plugin validate .` to check for errors

## License

MIT
