# Data Sources, Scans, and Findings

## Data sources

`SecretScanningDataSource`:

| Data source | Value | Required App Connection |
|-------------|-------|------------------------|
| GitHub | `github` | **`github-radar`** |
| GitLab | `gitlab` | `gitlab` |
| Bitbucket | `bitbucket` | `bitbucket` |

### The GitHub Radar requirement

GitHub scanning requires an App Connection of type **`github-radar`** — not `github`.

They are separate connection types installing separate GitHub Apps:

- `github` — for secret **syncs**, needs Secrets: write
- `github-radar` — for **scanning**, needs repository contents: read and push webhooks

A `github` connection will not work as a scanning data source. If a user reports that they created a
GitHub connection but cannot select it when adding a data source, this is why. See
`infisical-app-connections`.

### Resource scope

`SecretScanningResource`:

| Value | Meaning |
|-------|---------|
| `repository` | A single repository |
| `project` | A project/group containing repositories |

Scoping at `project` level picks up new repositories automatically as they are created, which is
usually what you want for ongoing coverage. Per-repository scoping is for targeted onboarding.

### Automatic scanning

All three data sources trigger scans on **push**. That is the ongoing coverage mechanism — a new
commit containing a credential produces a finding without anyone running anything.

## Scan types

`SecretScanningScanType`:

| Value | Meaning | Use for |
|-------|---------|---------|
| `full-scan` | Scans the entire repository, including history | Baseline when onboarding a repo |
| `diff-scan` | Scans only what changed | Automatic scans on push |

Run a **full scan** when first connecting a repository. Without it you only ever see leaks introduced
from that moment on, and the credential that has been sitting in `config.old.py` since 2019 goes
unnoticed.

Full scans on a large repository with deep history take time and produce a lot of findings at once.
Plan triage capacity before running one across an estate.

## Scan status

`SecretScanningScanStatus`:

| Value | Meaning |
|-------|---------|
| `queued` | Waiting to start |
| `scanning` | In progress |
| `completed` | Finished |
| `failed` | Did not finish |

A `failed` scan usually means the connection lost access — a revoked token, an uninstalled GitHub
App, or a repository that was deleted or made private.

## Findings

### Severity

`SecretScanningFindingSeverity`: `high`, `medium`, `low`

### Lifecycle

`SecretScanningFindingStatus`:

| Status | Meaning | When to use |
|--------|---------|-------------|
| `unresolved` | New, not yet triaged | Default state |
| `resolved` | Dealt with — the credential was rotated and the exposure closed | After actual remediation |
| `false-positive` | Not a secret at all | A test fixture, an example value, a random-looking string |
| `ignore` | A real secret, but intentionally accepted | Rare; document why |

Be precise about `resolved` versus `false-positive`. `resolved` means the credential was rotated.
Marking a real leak as resolved because the commit was deleted is wrong — the credential is still
live and still compromised.

`ignore` should be uncommon. A real secret that is deliberately in code is a decision worth
revisiting, not suppressing.

### What a finding carries

Findings include context: **file path, commit hash, and the scanning rule** that matched. The commit
hash is what you need to determine when the exposure began and therefore how long the credential has
been out.

## Responding to a real finding

Order matters:

1. **Rotate the credential.** It is compromised the moment it was pushed — anyone with a clone has it, and Git history persists in forks, CI caches, and local copies. See `infisical-secret-rotation`, or revoke and reissue.
2. **Move the secret into Infisical** so it stops being in code. See `infisical-setup`.
3. **Then** clean history if you want to, understanding this is hygiene rather than remediation.
4. **Mark the finding `resolved`.**

Do not lead with history rewriting. Users often want to `git filter-repo` first, which feels
productive and changes nothing about the credential's exposure.

## Noise reduction

The scanner uses **pattern matching, entropy analysis, and custom rules**. Tuning matters: a scanner
with a high false-positive rate gets ignored, and then real findings get ignored too.

### `infisical-scan:ignore`

Suppress a specific line by adding a trailing comment:

```javascript
console.log("8dyfuiRyq=vVc3RRr_edRk-fK__JItpZ"); // infisical-scan:ignore
```

Works in whatever comment syntax the language uses. Best tool for a genuine one-off false positive —
narrow, visible in review, and self-documenting.

### `.infisicalignore`

A file listing paths to exclude. Use for test fixtures, vendored dependencies, and generated files.

Be careful excluding whole directories. `.infisicalignore` on `test/` means a real credential
committed to a test helper is never found — and test files are a common place for real credentials to
end up.

### `.infisical-scan.toml`

The configuration file for rules, entropy thresholds, and allowlists.

Config precedence, highest first:

1. `--config` / `-c` flag
2. `INFISICAL_SCAN_CONFIG` environment variable
3. `<source>/.infisical-scan.toml`

If none is present, the default config is used.

Structure:

```toml
# Extend the default ruleset rather than replacing it
[extend]
path = "common_config.toml"

[[rules]]
# a custom rule
# entropy: minimum Shannon entropy a regex group must have to count as a secret
entropy = 3.5

[rules.allowlist]
# per-rule allowlist, to reduce false positives on this rule only

[allowlist]
# global allowlist — higher precedence than rule-specific allowlists
```

Points worth knowing:

- **Allowlist arrays are appended when extending**, and may contain repeated elements. Extending does not replace.
- The **global allowlist takes precedence** over rule-specific allowlists.
- **`entropy`** is a Shannon entropy floor. Secrets are usually made of random characters and so score high; raising the threshold cuts false positives but risks missing low-entropy secrets like a weak password.
- The default config is published at
  `https://raw.githubusercontent.com/Infisical/infisical/main/cli/config/infisical-scan.toml` —
  read it before writing custom rules, since the pattern you want may already exist.

Prefer **extending** the default config over writing one from scratch. A hand-rolled ruleset loses
coverage of the many credential formats the default already detects.

### Baselines

`--baseline-path` accepts a file of known findings to ignore. This is the practical way to adopt
scanning on a repository with a large backlog: baseline what exists, then fail the build only on
*new* findings, and work the backlog down separately.

Do not treat a baseline as remediation. Everything in it is still leaked.
