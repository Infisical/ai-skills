# The `infisical scan` CLI and Honey Tokens

## Why the CLI matters

Cloud data sources find leaks **after** a push. The CLI finds them **before**, if you wire it into a
pre-commit hook or CI. That is the difference between an incident and a caught mistake.

## `infisical scan`

Scans Git history by default.

```bash
# Scan the repository's git history
infisical scan

# Scan a directory that is not a git repo
infisical scan --no-git

# Verbose output showing each finding
infisical scan --verbose
```

### Flags

| Flag | Purpose |
|------|---------|
| `--source` / `-s` | Path to scan |
| `--no-git` | Treat the target as a plain directory, not a git repo |
| `--log-opts` | Pass git log options to narrow the commit range scanned |
| `--config` / `-c` | Config file path |
| `--baseline-path` | File of known findings to ignore |
| `--exit-code` | Exit code when leaks are found (**default 1**) |
| `--report-format` | Output format for the report |
| `--report-path` | Where to write the report |
| `--redact` | Redact secret values from output |
| `--max-target-megabytes` | Skip files larger than this |
| `--follow-symlinks` | Follow symlinks while scanning |
| `--pipe` | Read input from a pipe |
| `--no-color` | Disable colored output |
| `--verbose` | Show findings in detail |

Two flags to recommend by default:

- **`--redact`** whenever output might be captured — CI logs, shared terminals, pasted output. Without it the scanner prints the secret it found, which puts the secret in a new place.
- **`--report-format` / `--report-path`** in CI, so findings are an artifact rather than something buried in log scrollback.

`--log-opts` is how you scan a bounded range rather than all history, e.g. only commits on a branch.
Useful in CI to scan just the PR's commits.

## `infisical scan git-changes`

Scans uncommitted or staged changes rather than history.

```bash
# Scan uncommitted changes
infisical scan git-changes

# Scan only staged changes — what a pre-commit hook wants
infisical scan git-changes --staged

infisical scan git-changes --verbose
```

`--staged` is the flag that makes this useful in a pre-commit hook: it checks exactly what is about
to be committed.

Takes the same flags as `infisical scan` plus `--staged`.

## Pre-commit hook

```bash
infisical scan install --pre-commit-hook
```

Installs the scanner as a git pre-commit hook so a commit containing a secret is blocked locally.

**Important limitation to state plainly:** pre-commit hooks are advisory. Any developer can bypass
one with `git commit --no-verify`, and hooks are per-clone — a new clone has no hook until someone
installs it.

So a pre-commit hook is a **convenience that saves people from themselves**, not a control. Back it
with:

1. **CI scanning** that cannot be bypassed, failing the build on new findings
2. **A cloud data source** on the repository, catching anything that gets through

Recommend all three layers. They fail in different ways.

## CI integration

Scan staged or changed content in the pipeline and fail on findings:

```bash
infisical scan --redact --report-format json --report-path scan-report.json
```

`--exit-code` defaults to 1 when leaks are found, so the step fails naturally. Set it to `0` only if
you want a reporting-only stage that never blocks.

Adoption pattern for an existing repository with a backlog:

1. Run a full scan and write the findings to a baseline file
2. Pass `--baseline-path` in CI so only **new** findings fail the build
3. Work the baseline down separately

Without this, turning on CI scanning breaks every build immediately and the change gets reverted.

## Honey tokens

A different detection strategy. Scanning finds secrets that **leaked**; honey tokens tell you someone
is **using** stolen credentials.

### How they work

Honey tokens are **decoy credentials planted alongside your real secrets** so they look genuine. They
grant nothing. Any attempt to use one triggers an alert and notifies organization admins.

This catches the case scanning cannot: an attacker who already has access to your secret store. They
see a plausible AWS key, try it, and announce themselves.

### Provider support

**AWS IAM credentials only** at present. More providers are planned.

### Setup and permissions

- An organization admin must complete a **one-time setup** before honey tokens can be created
- **Creating, editing, resetting, and revoking** honey tokens requires project-level **Admin** by default
- **Members and Viewers can only view** them

Custom roles can adjust this — see the Permissions section of the honey tokens docs and
`infisical-access-control`.

### Creating one

In the Secret Manager dashboard, select the environment and secret path where the token should sit,
then **Add Honey Token**.

Placement is the whole design decision. A honey token is only useful where an attacker would find and
try it:

- **In the same paths as real secrets.** A honey token in an unused folder is never triggered.
- **Named plausibly.** `AWS_ACCESS_KEY_ID` next to your real credentials, not `HONEYPOT_DO_NOT_USE`.
- **Where legitimate systems will not touch it.** A false alarm from your own deployment script trains people to ignore the alert.

That last point is the tension: it must look real enough to tempt an attacker but not be picked up by
your own automation. Avoid planting one in a path that a `listSecrets` call renders wholesale into an
application's environment, because something will eventually try to use it.

### Responding to a trigger

A honey token alert means **someone has your secrets**. It is a high-confidence signal — there is no
benign reason to use a decoy credential. Treat it as a confirmed compromise of the secret store or of
a principal with access to it, and go to incident response rather than triaging it like a scanning
finding.
