**App Connection: `github-radar`**, not `github`. They install different GitHub Apps — `github` is for secret syncs (needs Secrets: write), `github-radar` is for scanning (needs repo contents: read + push webhooks). Trying to use an existing `github` connection as a scanning data source is the most common setup mistake here.

**Locally, to block commits before they happen:**

```bash
infisical scan install --pre-commit-hook
```

This installs a git pre-commit hook that runs `infisical scan git-changes --staged` and blocks a commit containing a secret.

**Full setup, in order:**

1. **Create a `github-radar` App Connection**, then add a Secret Scanning data source (`github`) pointing at it. Scope it at `project` (not `repository`) if you want new repos picked up automatically.
2. **Run a full scan** (`full-scan`) on each connected repo once, to baseline what's already leaked in history, not just new commits. Triage those findings before moving on.
3. **Leave automatic diff scanning on** — it fires on every push with no extra setup.
4. **Install the pre-commit hook** on developer machines (`infisical scan install --pre-commit-hook`).
5. **Back the hook with CI**, since pre-commit hooks can be skipped with `--no-verify` and don't exist until someone installs them on a fresh clone. In CI:
   ```bash
   infisical scan --redact --report-format json --report-path scan-report.json
   ```
   If the repo has an existing backlog, run a full scan first, save it as a baseline file, and pass `--baseline-path` in CI so only *new* findings fail the build.

That gives you three overlapping layers: hook (convenience), CI (enforcement), data source (catches anything that still gets through).

One thing worth flagging since it'll come up fast: when a finding is real, rotate the credential first, don't just mark it resolved because the commit got cleaned up. History rewriting doesn't un-leak something that's already been cloned. That's `infisical-secret-rotation` territory, happy to walk through it when you hit a real finding.
