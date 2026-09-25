# Agent bootstrap: connect a project without interactive prompts

Read this when **you are the one running the CLI**: an AI agent executing `infisical` commands in a
subprocess, with no terminal the user can type into. For a human following along in their own
terminal, use `cli-setup.md` instead.

Several CLI commands prompt interactively by default. The `infisical init` org and project pickers,
for example, hang or fail without a terminal. Every command below has a non-interactive form. Use
it.

## Before you start

Check the CLI supports this flow:

```bash
infisical projects --help
```

If that command is unknown, the installed CLI is too old. Upgrade it with the same package manager
it was installed with (see `cli-setup.md`), then check again.

## Step 1: Log in

Check for an existing session first:

```bash
infisical login status --json
```

If it reports an authenticated session for the right instance, skip to step 2. Note the session's
`domain`: you need it for the dashboard link in step 5.

Otherwise, **run `infisical login` yourself.** Don't ask the user to run it.

1. Tell the user a browser is about to open, and that they should log in there, **or sign up if they
   don't have an Infisical account yet**. New accounts complete the CLI login the same way.
2. Run the command with a subprocess timeout of **at least 10 minutes**:

   ```bash
   infisical login --domain https://app.infisical.com
   ```

   The command blocks until the user finishes in the browser, then exits on its own. The CLI gives
   up after 10 minutes, so a shorter subprocess timeout kills a login the user is still completing.
3. Pick the domain from what the user tells you:

   | User is on | `--domain` |
   |------------|------------|
   | US Cloud (default) | `https://app.infisical.com` |
   | EU Cloud | `https://eu.infisical.com` |
   | Self-hosted | Their instance URL, e.g. `https://infisical.example.com` |

4. If the command errors or times out (for example, no display server to open a browser), ask the
   user to run it so it logs in **your** session, not just theirs. In Claude Code, they can type
   `! infisical login --domain <domain>`, which runs in this session. In other agents, their terminal
   only helps if it shares your machine and user account.
5. Whoever ran it, **re-run `infisical login status --json` before continuing.** If it still reports
   no session, the login landed somewhere else (a different machine, container, or user). Stop and
   tell the user; don't continue with steps 2 to 5.

**Pick the organization.** If the user belongs to more than one organization, the browser shows an
org picker during login, and the CLI uses the org they pick. Before you create a project, check
which org is in use:

```bash
infisical org list --json
```

Each entry has `id`, `name`, `slug`, and `current`, which is `true` for the org the CLI is using.
Sub-organizations are nested under `subOrganizations`. If there's more than one org, confirm with
the user which one the project belongs in. To change it:

```bash
infisical org switch <org>
```

`<org>` can be the org's name, slug, or `id`. Always pass it: without it, `org switch` opens an
interactive picker. If the org requires MFA, the command prompts for a code, so ask the user to run
it in their own terminal.

If the user is on a self-hosted instance and sees no sign-up option, their admin has disabled
sign-up. They need an invite from their admin.

## Step 2: Link the directory to a project

If `.infisical.json` already exists in the directory, it's already linked, but check it's linked to
the right project before you import anything into it. The file holds no secrets, so you can read it:

1. Take its `workspaceId` and find it in `infisical projects list --json`. If it isn't there, the
   link is stale or belongs to an org or instance you're not logged into. Tell the user and ask
   whether to relink or switch org or domain.
2. If it is there, tell the user the project's name and confirm that's where they want the secrets.

**Relinking with `--force` replaces the whole file.** `init --project-id <id> --force` writes a file
with only `workspaceId`, dropping any `defaultEnvironment`, `gitBranchToEnvironmentMapping`,
`defaultSecretPath`, and `domain`. Before relinking, note which of those the old file had. Afterwards,
tell the user what was dropped and, if they want to keep it, add those fields back to the new file.

Then skip to step 3.

Otherwise, create a project and link it:

```bash
infisical projects create --name <project-name> --json
infisical init --project-id <id>
```

- Name the project after the repository directory unless the user asked for another name
- `projects create --json` prints the new project, including `id`, `name`, `slug`, and its
  `environments` (`dev`, `staging`, and `prod` by default)
- `--project-id` skips the interactive org and project pickers; without it, `init` opens them
- If the directory is already linked, `init` refuses to overwrite `.infisical.json` unless you add
  `--force`. Only add it if the user asked to relink the directory

To link an existing project instead of creating one, find its `id` with
`infisical projects list --json`, then run `infisical init --project-id <id>`.

`init --project-id` writes only the project ID (`workspaceId`). The file can also hold
`defaultEnvironment` and `gitBranchToEnvironmentMapping` (auto-selects an environment from the
current git branch), which `infisical run` and `infisical secrets set` use when you don't pass `--env`, plus
`domain` and `defaultSecretPath`. It holds no secrets, so it's safe to commit.

## Step 3: Import existing `.env` files

**Don't open, read, or print the user's `.env` files.** They hold secret values. Let the CLI parse
them. Don't delete them either, unless the user asks you to (see step 5).

First check which of these files exist, by name only:

`.env` · `.env.local` · `.env.development` · `.env.staging` · `.env.production`

Leave out templates such as `.env.example` or `.env.sample`. They hold placeholders, not secrets.
If no files exist, skip to step 4.

### Pick an environment for each file

You upload each file separately with `infisical secrets set --file`, so each file can go to its own
environment. **Always pass `--env`.** Without it, `secrets set` uses the environment mapped to the
current git branch in `.infisical.json`, then its `defaultEnvironment`, then `dev`. Neither is safe
to rely on: a branch mapping such as `main` → `prod` would send development values into production,
and an existing project may have no `dev`.

For a project you just created (its `environments` from `projects create --json` are `dev`,
`staging`, and `prod`):

| File | `--env` |
|------|---------|
| `.env`, `.env.development`, `.env.local` | `dev` |
| `.env.staging` | `staging` |
| `.env.production` | `prod` |

For an existing project, ask the user for the environment slug for each file (shown in the
dashboard's project settings). Don't pick one from the branch mapping or `defaultEnvironment`, and
don't guess. Confirm again before sending anything to an environment that looks like production
(`prod`, `production`).

**Files that share an environment overwrite each other.** If two files set the same key, the file
you upload later wins. Upload the `dev` files in the order `.env`, `.env.development`, `.env.local`,
so the most specific file wins, the same way most tools that load `.env` files layer them.

### Ask before uploading

Uploading sends secret values to a remote service, and `secrets set` doesn't ask for confirmation,
so the approval has to come from you. Tell the user which files you found, the project, and the
environment for each file, and wait for an explicit yes. Asking for "setup" or "the CLI" is not a
yes to uploading. If they decline, skip to step 4.

### Upload each file

Once they agree, run one command per file, in the order above:

```bash
infisical secrets set --file=<file> --env=<slug>
```

- **Never add `--output` or `--show-values`.** Both print the secret values, and `--output json`
  prints them unmasked. The default table masks every value as `******`
- **Don't pass `--path` expecting a directory.** On `secrets set`, `--path` is the folder inside
  Infisical to write to, not a local directory. Leave it out to write to the root folder

The table lists each key with a status:

| Status | Meaning |
|--------|---------|
| `SECRET CREATED` | The key didn't exist in that environment |
| `SECRET VALUE MODIFIED` | The key existed and now has this file's value |
| `SECRET VALUE UNCHANGED` | The key already had this value |

Report the key names and statuses to the user, per file. Two statuses need a closer look:

- **`SECRET VALUE MODIFIED` for a key an earlier file in this run created:** that earlier file's
  value was overwritten. List those keys and files for the user
- **`SECRET VALUE MODIFIED` in an existing project:** the upload replaced a value that was already in
  Infisical. Tell the user which keys changed so they can check the old values weren't needed

**If a file fails, nothing from that file is uploaded.** The CLI checks the whole file first. Common
errors:

- `Secret key '<KEY>' has an empty value`: the file has a line like `DEBUG=`. Ask the user to give
  the key a value or remove it, then upload the file again. Don't edit the file yourself
- `secret key 'export <KEY>' cannot contain spaces`: the file uses `export KEY=value` lines. Ask the
  user to remove the `export` prefixes, or skip the file
- `invalid format, expected key=value in line: ...`: usually a value that spans several lines, such
  as a private key. **This error prints the line from the file, which may be part of a secret. Don't
  repeat it.** Tell the user which file has a line the CLI can't parse, and suggest adding that value
  in the dashboard instead

### Keep the files out of git

Skip this if the directory isn't a git repository (`git rev-parse --is-inside-work-tree` fails).
Otherwise, for each file you uploaded, check whether git ignores it and whether it's tracked:

```bash
git check-ignore -q <file> || echo "not ignored"
git ls-files -- <file>
```

- **Not ignored:** add the file name to `.gitignore` (create the file if it doesn't exist), and tell
  the user you did
- **Listed by `git ls-files`:** the file is already committed. `.gitignore` only stops untracked
  files from being added, so its values are already in the repository's history, and ignoring or
  deleting the file now doesn't remove them. Tell the user plainly: they should untrack it with
  `git rm --cached <file>`, and treat those secrets as exposed and rotate them, especially if the
  repository has been pushed anywhere

### If your permission system blocks the upload

Some agents block commands that send the contents of a secrets file to a remote service unless the
user explicitly asked for it. Claude Code's auto mode does this. That check is doing its job, so
**don't retry, and don't try another command that uploads the same file.**

Instead, give the user the exact commands and ask them to run them:

```bash
infisical secrets set --file=<file> --env=<slug>
```

In Claude Code, the user can type `! infisical secrets set --file=<file> --env=<slug>` so the
command runs in the session and you can read the table. In other agents, ask the user to run the
commands in their terminal and paste the tables back. Then continue with the checks above.

## Step 4: Run the app with secrets

Find the command the user starts the app with (`package.json` scripts, `Makefile`, `Procfile`, or
equivalent) and give them the wrapped version. Without `--env`, `run` uses the environment mapped
to the current git branch in `.infisical.json`, then its `defaultEnvironment`, then `dev`. Whether
to pass `--env` depends on what happened in step 3:

- **You imported secrets:** pass the slug the development files went to, even if it's `dev`.
  Otherwise the branch mapping or `defaultEnvironment` may pick a different environment from where
  the secrets went:

  ```bash
  infisical run --env=<slug> -- <start command>
  ```

- **No import** (no `.env` files, or the user declined): don't add `--env`. Leave the project's own
  selection in charge, so a branch mapping keeps working:

  ```bash
  infisical run -- <start command>
  ```

  If `.infisical.json` has no mapping or `defaultEnvironment`, this uses `dev`. For an existing
  project, check with the user that `dev` exists and is the right environment. If it isn't, pass
  the slug they give you

For example, `infisical run --env=dev -- npm run dev` after importing into `dev`. Mention that:

- `infisical secrets` lists the project's secrets, and `infisical secrets set KEY=value` adds one
- `--env <slug>` switches environments, e.g. `infisical run --env=staging -- npm start`
- They can view and edit everything in the Infisical dashboard

Don't run `infisical secrets` yourself to "check" the import. It prints secret values into your
context. The `secrets set` tables already tell you what was uploaded.

## Step 5: Tell the user where their secrets are now

If you imported secrets, tell the user they now live in their Infisical project, and link to them:

```
<domain>/organizations/<orgId>/projects/secret-management/<projectId>/secrets/<env>
```

- `<domain>` is the session's `domain` from `infisical login status --json` (without a trailing
  `/api`). That covers both a fresh login and a reused session
- `<orgId>` and `<projectId>` are the `orgId` and `id` fields from `projects create --json` (or the
  matching entry in `projects list --json`, if you linked an existing project)
- `<env>` is the environment you passed to `--env`. If files went to more than one environment, give
  a link for each

Then **strongly recommend deleting the imported `.env` files.** Infisical is now the source of
truth for those values, and `infisical run` injects them. A plaintext copy on disk is one more place
the secrets can leak from, and it drifts out of date as soon as someone changes a value in
Infisical.

Make the recommendation specific:

- Name only files whose `secrets set` command succeeded. If a file failed, say so and don't
  recommend deleting it
- Don't recommend deleting a file that shares a key with a file uploaded after it to the same
  environment. Its value for that key was overwritten, so the file may be the only copy. The user
  resolves the conflict first
- Suggest they first confirm the app starts with the `infisical run` command from step 4
- A working start command doesn't prove nothing else needs the file. Search for the file names
  everywhere they might be loaded directly:
  - `docker-compose.yml` (`env_file:`), `docker compose --env-file`, `docker run --env-file`, and
    `Dockerfile`
  - Test setup and config (for example, a `dotenv` or `dotenv-flow` load in a test helper, or a test
    runner option pointing at a `.env` file)
  - CI workflows and scripts that load or `source` the file

  If something does, tell the user it needs to switch to `infisical run` (or `infisical export`)
  before they delete the file

Let the user decide. If they ask you to delete the files, remove them with `rm` without opening them.

## Then suggest next steps

Based on what's in the repository, suggest what fits. If a suggestion names another skill and it
isn't installed, give the user its install command, e.g.
`npx skills add Infisical/ai-skills --skill infisical-secret-syncs`.

- A `Dockerfile` → secrets in containers (`docker-integration.md`)
- CI config such as `.github/workflows/` → secrets in CI with a machine identity
  (`cicd-integration.md`)
- Kubernetes manifests or Helm charts → `infisical-kubernetes-operator`
- Secrets that also live in a hosting provider (Vercel, AWS, and so on) → `infisical-secret-syncs`
- Teammates → they can invite them from the dashboard
