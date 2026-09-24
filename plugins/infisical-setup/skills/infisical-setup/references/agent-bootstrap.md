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

If it reports an authenticated session for the right instance, skip to step 2.

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
   user to run the same command in their own terminal, then continue once they confirm.

**The organization is chosen in the browser.** If the user belongs to more than one organization,
the browser shows an org picker during login, and every later command acts in the org they pick.
There is no CLI flag to switch orgs afterwards. To use a different org, run `infisical login` again
and have the user pick that org.

`infisical org list --json` lists the user's orgs (`id` and `name`). Use it to tell the user which
orgs exist, not to select one.

If the user is on a self-hosted instance and sees no sign-up option, their admin has disabled
sign-up. They need an invite from their admin.

## Step 2: Link the directory to a project

If `.infisical.json` already exists in the directory, it's already linked. Skip to step 3.

Otherwise, create a project and link it:

```bash
infisical projects create --name <project-name> --json
infisical init --yes --project-id <id>
```

- Name the project after the repository directory unless the user asked for another name
- `projects create --json` prints the new project, including `id`, `name`, `slug`, and its
  `environments` (`dev`, `staging`, and `prod` by default)
- `init --yes` requires `--project-id`; without it, `init` falls back to the interactive pickers

To link an existing project instead of creating one, find its `id` with
`infisical projects list --json`, then run `infisical init --yes --project-id <id>`.

`.infisical.json` holds only the project ID. It's safe to commit.

## Step 3: Import existing `.env` files

**Don't open, read, or print the user's `.env` files.** They hold secret values. Let the CLI parse
them. Don't delete them either, unless the user asks you to (see step 5).

First check which of these files exist, by name only:

`.env` · `.env.local` · `.env.development` · `.env.staging` · `.env.production`

These are the only names `infisical import` looks for. It ignores `.envrc` and other dotfiles.

**`import` sends every file it finds into one environment.** It doesn't map `.env.production` to
`prod`. If the same key appears in two files, the file imported later overwrites the earlier value,
and `.env.production` is imported last. So:

- **Only `.env`, `.env.local`, or `.env.development` exist:** import them into `dev`:

  ```bash
  infisical import --yes --add-gitignore --json
  ```

- **`.env.staging` or `.env.production` also exist:** don't run the import yet. Tell the user those
  files would be merged into a single environment, and ask how they want to proceed. For example,
  they can temporarily move the staging and production files aside and import only the development
  ones.

Flags:

| Flag | Effect |
|------|--------|
| `--yes` | Skips the confirmation prompt. Required when you run it |
| `--add-gitignore` | Adds each imported file to `.gitignore` if it isn't already covered |
| `--env <slug>` | Target environment (default: `dev`) |
| `--path <dir>` | Directory to scan (default: current directory) |
| `--json` | Machine-readable summary |

The `--json` summary lists each file with its target `env`, the key **names** found, and the
`uploaded` count, plus which files were added to `.gitignore`. Report that summary to the user. It
never includes values. The source files are left in place.

If no files exist, skip this step.

### If your permission system blocks the import

Some agents block commands that send the contents of a secrets file to a remote service unless the
user explicitly asked for it. Claude Code's auto mode does this. That check is doing its job, so
**don't retry the import, and don't substitute another command that uploads the same files**, such
as `infisical secrets set --file=.env`.

Instead, give the user the exact command and ask them to run it:

```bash
infisical import --yes --add-gitignore --json
```

In Claude Code, the user can type `! infisical import --yes --add-gitignore --json` so the command
runs in the session and you can read its output. In other agents, ask the user to run it in their
terminal and paste the JSON summary back. Then continue with step 4 using that summary.

## Step 4: Run the app with secrets

Find the command the user starts the app with (`package.json` scripts, `Makefile`, `Procfile`, or
equivalent) and give them the wrapped version:

```bash
infisical run -- <start command>
```

For example, `infisical run -- npm run dev`. Mention that:

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

- `<domain>` is the value you passed to `infisical login --domain`
- `<orgId>` and `<projectId>` are the `orgId` and `id` fields from `projects create --json` (or the
  matching entry in `projects list --json`, if you linked an existing project)
- `<env>` is the environment the import used, usually `dev`

Then **strongly recommend deleting the imported `.env` files.** Infisical is now the source of
truth for those values, and `infisical run` injects them. A plaintext copy on disk is one more place
the secrets can leak from, and it drifts out of date as soon as someone changes a value in
Infisical.

Make the recommendation specific:

- Name only files the import summary shows as fully uploaded (no `error`, and `uploaded` matches the
  number of `keys`). If any file failed, say so and don't recommend deleting it
- Suggest they first confirm the app starts with the `infisical run` command from step 4
- Check whether anything reads those files directly, not through the environment. Look for the file
  names in `docker-compose.yml` (`env_file:`), `Dockerfile`, and scripts that load them explicitly.
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
