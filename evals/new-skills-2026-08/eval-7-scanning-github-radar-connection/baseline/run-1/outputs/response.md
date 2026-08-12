**GitHub Secret Scanning (platform side):** you need a **GitHub App Connection**, not the plain GitHub OAuth App Connection. Secret Scanning needs the App Connection's webhook subscription on push events plus read access to repo contents and commit history, which only the GitHub App integration type provides.

Setup:
1. Org Settings > App Connections > New Connection > GitHub > choose the "GitHub App" method (not OAuth).
2. Install the Infisical GitHub App on your org and pick which repos it can access.
3. In the Secret Scanning module, add a data source using that App Connection and select the repos to monitor.
4. Infisical scans the full git history on the initial pass, then listens on the webhook for new pushes going forward and alerts on findings.

**Stopping secrets at commit time (local):**
1. Install the Infisical CLI (`brew install infisical/get-cli/infisical` on macOS, or the equivalent for your platform).
2. From inside each repo, run:
   ```
   infisical scan install --pre-commit-hook
   ```
   This installs a git pre-commit hook that runs Infisical's gitleaks-based scanner against staged changes on every `git commit` and blocks the commit if it detects a secret.
3. Developers can also run `infisical scan` manually to check the whole repo/history, which is worth doing once when rolling this out to catch anything already committed.

Since CLI flags do shift between versions, run `infisical scan --help` after installing to confirm the exact subcommand on the version you're on before rolling it out org-wide.
