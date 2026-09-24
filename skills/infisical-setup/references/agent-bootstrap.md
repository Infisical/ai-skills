# Agent bootstrap: connect a project without interactive prompts

Read this when **you are the one running the CLI**: an AI agent executing `infisical` commands in a
subprocess, with no terminal the user can type into. For a human following along in their own
terminal, use `cli-setup.md` instead.

Several CLI commands prompt interactively by default. The `infisical init` org and project pickers
and the `infisical import` confirmation hang or fail without a terminal. Every command below has a
non-interactive form. Use it.

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
current git branch), which `infisical run` and `import` use when you don't pass `--env`, plus
`domain` and `defaultSecretPath`. It holds no secrets, so it's safe to commit.

## Step 3: Import existing `.env` files

**Don't open, read, or print the user's `.env` files.** They hold secret values. Let the CLI parse
them. Don't delete them either, unless the user asks you to (see step 5).

First check which of these files exist, by name only:

`.env` · `.env.local` · `.env.development` · `.env.staging` · `.env.production`

These are the only names `infisical import` looks for. It ignores `.envrc` and other dotfiles.

**`import` sends every file it finds into one environment.** It doesn't map `.env.production` to
`prod`. If the same key appears in two files, the file imported later overwrites the earlier value,
and `.env.production` is imported last. If `.env.staging` or `.env.production` exist, don't import
yet. Tell the user those files would be merged into a single environment, and ask how they want to
proceed. For example, they can temporarily move the staging and production files aside and import
only the development ones.

**Pick the target environment and always pass it with `--env`.** Without `--env`, `import` uses the
environment mapped to the current git branch in `.infisical.json`, then its `defaultEnvironment`,
then `dev`. Neither is safe to rely on: a branch mapping such as `main` → `prod` would send
development `.env` files into production, and an existing project may have no `dev`.

- Project you just created: `dev` (it's in the `environments` list from `projects create --json`)
- Existing project: ask the user for the slug of the environment these files belong in (shown in the
  dashboard's project settings). Don't pick one from the branch mapping or `defaultEnvironment`, and
  don't guess. If the answer looks like production (`prod`, `production`), confirm again

**Ask before uploading.** Importing sends secret values to a remote service, and `--yes` skips the
CLI's own confirmation, so the approval has to come from you. Tell the user which files you found,
the project, and the environment, and wait for an explicit yes. Asking for "setup" or "the CLI" is
not a yes to uploading. If they decline, skip to step 4.

Once they agree:

```bash
infisical import --env <slug> --yes --add-gitignore --json
```

Flags:

| Flag | Effect |
|------|--------|
| `--yes` | Skips the CLI confirmation prompt. Required when you run it, and why you ask first |
| `--add-gitignore` | Adds each imported file to `.gitignore` if it isn't already covered |
| `--env <slug>` | Target environment (default: branch mapping, then `defaultEnvironment` from `.infisical.json`, then `dev`). Always pass it |
| `--path <dir>` | Directory to scan (default: current directory) |
| `--json` | Machine-readable summary |

The `--json` summary lists each file with its target `env`, the key **names** found, and the
`uploaded` count, plus which files were added to `.gitignore`. Report that summary to the user. It
never includes values. The source files are left in place.

Check the summary for **key names that appear in more than one file**. Only the value from the file
imported last survived, even though every file reports a full `uploaded` count. List those keys and
files for the user.

**Check whether the imported files are tracked by git:**

```bash
git ls-files -- <file> ...
```

`.gitignore` only stops untracked files from being added. If a file is listed, its values are
already in the repository's history, and ignoring or deleting it now doesn't remove them. Tell the
user plainly: they should untrack it with `git rm --cached <file>`, and treat those secrets as
exposed and rotate them, especially if the repository has been pushed anywhere.

If no files exist, skip this step.

### If your permission system blocks the import

Some agents block commands that send the contents of a secrets file to a remote service unless the
user explicitly asked for it. Claude Code's auto mode does this. That check is doing its job, so
**don't retry the import, and don't substitute another command that uploads the same files**, such
as `infisical secrets set --file=.env`.

Instead, give the user the exact command and ask them to run it:

```bash
infisical import --env <slug> --yes --add-gitignore --json
```

In Claude Code, the user can type `! infisical import --env <slug> --yes --add-gitignore --json` so the command
runs in the session and you can read its output. In other agents, ask the user to run it in their
terminal and paste the JSON summary back. Then continue with step 4 using that summary.

## Step 4: Run the app with secrets

Find the command the user starts the app with (`package.json` scripts, `Makefile`, `Procfile`, or
equivalent) and give them the wrapped version, with the same `--env` you imported into:

```bash
infisical run --env=<slug> -- <start command>
```

For example, `infisical run --env=dev -- npm run dev`. Keep `--env` even when the slug is `dev`:
without it, `run` picks the branch-mapped environment or `defaultEnvironment` from `.infisical.json`,
which may not be where the secrets went. Mention that:

- `infisical secrets` lists the project's secrets, and `infisical secrets set KEY=value` adds one
- `--env <slug>` switches environments, e.g. `infisical run --env=staging -- npm start`
- They can view and edit everything in the Infisical dashboard

Don't run `infisical secrets` yourself to "check" the import. It prints secret values into your
context. The import summary already tells you what was uploaded.

## Step 5: Tell the user where their secrets are now

If you imported secrets, tell the user they now live in their Infisical project, and link to them:

```
<domain>/organizations/<orgId>/projects/secret-management/<projectId>/secrets/<env>
```

- `<domain>` is the session's `domain` from `infisical login status --json` (without a trailing
  `/api`). That covers both a fresh login and a reused session
- `<orgId>` and `<projectId>` are the `orgId` and `id` fields from `projects create --json` (or the
  matching entry in `projects list --json`, if you linked an existing project)
- `<env>` is the environment you passed to `--env`

Then **strongly recommend deleting the imported `.env` files.** Infisical is now the source of
truth for those values, and `infisical run` injects them. A plaintext copy on disk is one more place
the secrets can leak from, and it drifts out of date as soon as someone changes a value in
Infisical.

Make the recommendation specific:

- Name only files the import summary shows as fully uploaded (no `error`, and `uploaded` matches the
  number of `keys`). If any file failed, say so and don't recommend deleting it
- Don't recommend deleting a file that shares a key with a file imported after it. Its value for
  that key was overwritten, so the file may be the only copy. The user resolves the conflict first
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
