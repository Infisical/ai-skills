# CLI Setup for Local Development

The Infisical CLI is the fastest way to get secrets into a local development workflow. It injects secrets as environment variables into any process — no code changes needed.

## Installation

Guide the user based on their OS:

| Platform | Command |
|----------|---------|
| macOS | `brew install infisical/get-cli/infisical` |
| Debian/Ubuntu | `curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' \| sudo -E bash` then `sudo apt-get update && sudo apt-get install -y infisical` |
| RedHat/CentOS/Amazon | `curl -1sLf 'https://artifacts-cli.infisical.com/setup.rpm.sh' \| sudo -E bash` then `sudo yum install infisical` |
| Alpine | `apk add --no-cache bash sudo wget` then `wget -qO- 'https://artifacts-cli.infisical.com/setup.apk.sh' \| sudo sh` then `apk update && sudo apk add infisical` |
| Arch Linux | `yay -S infisical-bin` |
| Windows (Scoop) | `scoop bucket add org https://github.com/Infisical/scoop-infisical.git` then `scoop install infisical` |
| Windows (Winget) | `winget install infisical` |
| npm (any platform) | `npm install -g @infisical/cli` |

Notes that trip people up:
- The Alpine setup script is **`setup.apk.sh`** (not `setup.alpine.sh`), and it's fetched with
  `wget` piped to `sh`. Alpine also needs `bash`, `sudo`, and `wget` present first.
- Scoop requires **adding the Infisical bucket first**; `scoop install infisical` alone fails.
- Linux repos moved from Cloudsmith to `artifacts-cli.infisical.com`. The old Cloudsmith
  repository stops serving on **September 16, 2026** — machines still pointed at it will fail to
  install or update.

For production or CI, pin to a specific version for consistency.

Updating: `brew update && brew upgrade infisical`, `scoop update infisical`,
`npm update -g @infisical/cli`.

## Login

```bash
# Browser-based login (default — opens browser)
infisical login

# Interactive terminal login (useful in containers, WSL2, Codespaces)
infisical login --interactive

# Machine identity login (for automated environments)
infisical login --method=universal-auth \
  --client-id=<client-id> \
  --client-secret=<client-secret>
```

The CLI stores tokens in the system keyring. Users can switch between accounts with `infisical user`.

### Self-hosted or EU Cloud

By default the CLI connects to `https://app.infisical.com`. To use a different instance:

```bash
# Option 1: Environment variable (recommended)
export INFISICAL_API_URL="https://your-instance.com"

# Option 2: Flag on every command
infisical login --domain="https://your-instance.com"

# Option 3: Interactive login prompts for region
infisical login
```

## Initialize a project

```bash
cd /path/to/your/project
infisical init
```

`infisical init` opens interactive org and project pickers. If you're an agent running the command
yourself, use `infisical init --project-id <id>` instead (see `agent-bootstrap.md`).

This creates `.infisical.yaml`, a non-sensitive file that links the directory to an Infisical project. Safe to commit to git. Older CLIs wrote `.infisical.json` instead; the CLI still reads it when there's no `.infisical.yaml`, and `infisical migrate-config` converts it.

```yaml
secrets-management:
  project-id: 63ee5410a45f7a1ed39ba118
  default-environment: dev
  mappings:
    git-branch-to-environment:
      main: prod
      staging: staging
      develop: dev
```

The `git-branch-to-environment` mapping is optional but convenient: it auto-selects the environment based on the current git branch.

## Run your app with secrets

```bash
# Basic — injects all secrets from the project as env vars
infisical run -- npm run dev

# Specify environment
infisical run --env=staging -- npm run dev

# Specify a folder path within the project
infisical run --path=/apps/backend -- npm run dev

# Multiple paths — repeat the flag to merge secrets from several folders
infisical run --path=/common --path=/nextjs -- npm run dev

# Watch mode — auto-restarts when secrets change
infisical run --watch -- npm run dev

# Multiple chained commands
infisical run --command="npm run build && npm run start"
```

This works with any framework or language — the secrets appear as standard environment variables in the child process.

## The `secrets-manager` command namespace

Secrets Management commands live under `infisical secrets-manager` (short alias `sm`), in the shape
`infisical secrets-manager <resource> <action>`. Resources are `secrets`, `folders`, `environments`,
and `projects`. Actions are `get`, `create`, `update`, and `delete`:

- `get` with no name lists; `get <name>` shows one. There's no separate `list`
- `create` fails if the item already exists, and `update` fails if it doesn't. Neither writes
  anything when it fails
- What you act on is positional (`environments delete qa`). Where you act is a flag: `--projectId`,
  `--env`, `--path`, each falling back to its environment variable (`INFISICAL_PROJECT_ID`,
  `INFISICAL_ENVIRONMENT`, `INFISICAL_SECRET_PATH`) and then `.infisical.yaml`
- **Exception for machine identities:** `secrets get`, `run`, and `export` take the project only
  from `--projectId` or `INFISICAL_PROJECT_ID`, never from `.infisical.yaml` (`secrets create` and
  `update` do read the file). In CI, pass `--projectId`. A service token always uses its own project

`run` and `export` also work as `infisical secrets-manager run` / `export`. The legacy top-level
`infisical secrets`, `run`, `export`, and `dynamic-secrets` commands keep working unchanged.

## Manage secrets from the CLI

```bash
# List all secrets (get with no names lists)
infisical secrets-manager secrets get

# Get specific secrets
infisical secrets-manager secrets get API_KEY DATABASE_URL

# Create secrets: fails with secret_exists, writing nothing, if any key already exists
infisical secrets-manager secrets create API_KEY=sk-1234 DATABASE_URL=postgres://...

# Value from a file
infisical secrets-manager secrets create CERT=@/path/to/cert.pem

# Bulk create from a .env or YAML file
infisical secrets-manager secrets create --file=./.env

# Change existing secrets: fails with secret_not_found, writing nothing, if any key is missing
infisical secrets-manager secrets update API_KEY=sk-5678

# Delete secrets (asks you to type the name; -y/--yes skips the question)
infisical secrets-manager secrets delete API_KEY
```

- `create` and `update` check every `NAME=value` argument before any request, so nothing (not even a
  `--tag`) is created for a write that would fail. `invalid_argument` covers the same key given twice
  (in arguments or in the `--file`), an argument with no name or no value, and a name starting with
  a digit. The error names the key, never the value. Problems inside a `--file` (an empty value,
  a line it can't parse) still print as free text
- `secrets delete` defaults to `--type personal`. Pass `--type shared` to delete a shared secret
- With a machine identity or service token, `create` and `update` expand `@filepath` and fall back
  to `.infisical.yaml` for the project, like a login session. A service token can only write to its
  own project (`token_project_mismatch`)

**Use `create` and `update`, not `set`.** `infisical secrets set` (and the hidden
`infisical secrets-manager secrets set`) still work, but they upsert: they create or silently
overwrite. With `create` and `update`, an overwrite is always a deliberate choice.

To import a `.env` file into an environment that may already have some of its keys (for example,
layering `.env.local` over `.env`):

1. `secrets create --file=<file>`. If it fails with `secret_exists`, nothing was written, and the
   error lists every key that already exists
2. If those values should be replaced, `secrets update --file=<file>`. It succeeds only when every
   key in the file exists
3. If `update` then fails with `secret_not_found`, the file mixes new and existing keys. Split it
   into one file for `update` and one for `create`, or add the values in the dashboard

The legacy top-level forms are unchanged: `infisical secrets` lists, `infisical secrets delete`
deletes **without asking**, and `infisical secrets generate-example-env > .example-env` writes an
example file with redacted values.

## Projects, environments, and folders

```bash
# Projects: list, show one (by slug or ID, with its environments), create, update, delete
infisical secrets-manager projects get
infisical secrets-manager projects get my-app
infisical secrets-manager projects create --name my-app            # dev, staging, prod by default
infisical secrets-manager projects update my-app --name "My App"   # also --slug, --description
infisical secrets-manager projects delete my-app

# Environments of a project
infisical secrets-manager environments get --projectId <project-id>
infisical secrets-manager environments create qa --name "QA" --projectId <project-id>
infisical secrets-manager environments update qa --slug testing --projectId <project-id>
infisical secrets-manager environments delete qa --projectId <project-id>

# Folders at a path in an environment
infisical secrets-manager folders get --env prod --path /backend
infisical secrets-manager folders create api --env prod --path /backend
infisical secrets-manager folders update api --name public-api --env prod --path /backend
infisical secrets-manager folders delete api --env prod --path /backend --projectId <project-id>
```

- **`projects get` with no argument lists the org's projects.** It never falls back to
  `INFISICAL_PROJECT_ID` or `.infisical.yaml`. To see the linked project, pass its ID (from
  `infisical profile current`)
- `projects delete` refuses a project with delete protection on (`project_delete_protected`)
- `environments delete` soft-deletes: the slug stays taken until the grace period ends
  (`environment_pending_deletion` if you try to reuse it). `--force` deletes permanently now
- Folder names are letters, numbers, `-`, and `_` only. Put a nested location in `--path`, not in
  the name (`folders create a/b` is `invalid_argument`). `folders update` needs `--name` or
  `--description` (`nothing_to_update` otherwise); `--description ""` clears it
- `folders delete` removes the folder **and everything inside it**
- Projects and environments reject service tokens (`service_token_not_supported`). Use a login
  session or a machine identity access token (`--token`)
- The older `infisical secrets folders get|create|delete` still works. Its copy under
  `secrets-manager secrets folders` is hidden; use `secrets-manager folders`

## Deletes ask first

Every `delete` under `secrets-manager` asks you to type the name, slug, or (for several secrets)
the count of what's being deleted. The question goes to stderr.

- `-y` / `--yes` skips the question, for scripts and agents
- **Without a terminal and without `--yes`, nothing is deleted.** The command fails with
  `confirmation_required` and suggests the same command with `--yes`. A wrong answer is
  `confirmation_declined`
- `projects delete`, `environments delete`, and `folders delete` **never** use an implicit project:
  `environments` and `folders` deletes need an explicit `--projectId` (`project_required`), even if
  `INFISICAL_PROJECT_ID` or `.infisical.yaml` is set. `secrets delete` and
  `dynamic-secrets lease delete` keep their fallbacks, and the question names the project and where it
  came from
- `--force` skips a safeguard such as the grace period. It never skips the question

## Check what commands here will use

```bash
infisical profile current
```

Prints the profile, org, and domain, then the Secrets Management defaults with where each came from:
`Project:` / `Project via:`, `Environment:` / `Environment via:`, `Secret path:` /
`Secret path via:`, and the `Project config:` file path. Each `via:` line ends with the flag that
overrides it, e.g. `Environment via: default (override with --env)`. When the project comes from
the config file, the hint adds `machine identities may ignore it`: with a machine identity, `run`,
`export`, and `secrets get` don't read the project from the file. Use it before a write to confirm
secrets will land in the right place. `Project: unknown` means `.infisical.yaml` exists but can't be read;
commands that need a project then fail with `project_config_invalid` instead of running unlinked.

## Errors in scripts

`secrets-manager` CRUD commands take `-o json` or `-o yaml`. Data goes to stdout; tips and errors go
to stderr. With `-o json`, an error is JSON on stderr and the exit code is `1`:

```json
{"error": {"code": "environment_not_found", "message": "...", "next": ["infisical secrets-manager environments get --projectId 6f1c2a3e-..."]}}
```

Branch on `code`, which is stable; never on `message`. `next` holds complete commands that fix the
error. Suggested commands never contain a token or secret value (they show `<value>` instead).

| Code | Meaning |
|------|---------|
| `auth_required` | No session, or the token is invalid or expired |
| `permission_denied` | The role doesn't allow the action |
| `project_not_linked` | No `--projectId`, `INFISICAL_PROJECT_ID`, or `.infisical.yaml` |
| `project_config_invalid` | `.infisical.yaml` (or legacy `.infisical.json`) exists but can't be read |
| `project_not_found` | The project doesn't exist, or you aren't a member |
| `project_type_not_supported` | The project belongs to another product |
| `project_required` | A delete ran without an explicit `--projectId` |
| `environment_not_found` / `environment_exists` / `environment_pending_deletion` | Environment slug missing, taken, or held by a pending deletion |
| `secret_exists` / `secret_not_found` | `secrets create` on an existing key / `secrets update` on a missing one |
| `folder_exists` / `folder_not_found` | Folder name taken / missing at `--path` |
| `nothing_to_update` | `update` with no change flags |
| `invalid_flag_value` / `invalid_argument` | A flag or argument the command can't use. Nothing is sent |
| `service_token_not_supported` | The command's routes reject service tokens |
| `token_project_mismatch` | A service token for a different project than the one selected |
| `project_delete_protected` | `projects delete` on a delete-protected project |
| `confirmation_required` / `confirmation_declined` | A delete ran without a terminal and without `--yes` / the typed answer didn't match |

Errors from the legacy top-level commands still print as free text.

## Export secrets to files

```bash
# .env format (default)
infisical export > .env

# Shell-ready (with export keyword)
infisical export --format=dotenv-export > .env

# JSON
infisical export --format=json > secrets.json

# YAML
infisical export --format=yaml > secrets.yaml
```

## Useful flags (apply to most commands)

| Flag | Purpose |
|------|---------|
| `--env` | Environment slug (default: `dev`) |
| `--path` | Folder path within the project (default: `/`). Repeatable — merges multiple folders |
| `--projectId` | Project ID (default: `INFISICAL_PROJECT_ID`, then `.infisical.yaml`; with a machine identity, `run`/`export`/`secrets` skip the file, so pass it) |
| `--expand` | Expand `${VAR}` references (default: true) |
| `--include-imports` | Include imported secrets (default: true) |
| `--tags` | Filter by comma-separated tags |
| `--token` | Machine identity token (alternative to `INFISICAL_TOKEN` env var) |

## Beyond local dev

The CLI covers more than `run`/`secrets`/`export`. Other command groups you may need:

| Command | Purpose |
|---------|---------|
| `infisical secrets-manager` (`sm`) | Secrets, folders, environments, projects, dynamic secrets, `run`, `export` (see above) |
| `infisical profile current` | Show the profile, org, project, environment, and path commands here use |
| `infisical dynamic-secrets` | Lease, renew, and revoke dynamic secrets |
| `infisical gateway` / `infisical relay` | Run a Gateway or Relay for private-network access |
| `infisical agent` | Run the Infisical Agent daemon (see the `infisical-agent` skill) |
| `infisical agent-proxy` | Local or standalone secret-serving proxy |
| `infisical bootstrap` | Automated instance bootstrapping for self-hosted setups |
| `infisical vault` | Manage the local CLI credential vault backend |
| `infisical pam` | Privileged access management sessions |
| `infisical kmip` | KMIP client operations |
| `infisical scan` | Secret scanning (see below) |

## Secret scanning

The CLI can scan for leaked secrets in git history:

```bash
# Scan git history
infisical scan

# Scan only staged changes (pre-commit)
infisical scan git-changes --staged

# Install as git pre-commit hook
infisical scan install --pre-commit-hook
```

## Offline support

The CLI caches previously fetched secrets. If the Infisical server is unreachable, `infisical run` falls back to the cache automatically.

## Terminal security tip

Prevent secrets from appearing in shell history:

```bash
# Add to ~/.bashrc or ~/.zshrc
export HISTIGNORE="*infisical secrets set*:*infisical secrets-manager secrets*:*infisical sm secrets*:$HISTIGNORE"
```
