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
infisical secrets-manager projects get --help
```

If the output doesn't show `get [slug-or-id]`, the installed CLI is too old. Older versions report
an unknown command or print a general help page, and may still exit successfully, so check the
output rather than the exit code. Upgrade the CLI with the same package manager it was installed
with (see `cli-setup.md`), then check again.

`sm` is a short alias for `secrets-manager`. This guide uses the full name, which is what the CLI's
own help and suggested commands use.

**Use `-o json` on the `secrets-manager` commands below**, except `secrets create` and
`secrets update`, whose `-o json` output prints secret values (see step 3). Data goes to stdout. A
failure the CLI recognizes goes to stderr as
`{"error": {"code": "...", "message": "...", "next": ["<command>"]}}` and exits `1`. Act on `code`,
not the message text. `next` lists complete commands that fix the error, with any secret value
written as `<value>`.

**Not every failure has a code.** An API error the CLI doesn't recognize still prints as plain text
on stderr, even with `-o json`: a `Response Code:` line and the server's `Message:`. Treat stderr
that isn't JSON as an error without a code: tell the user what the message says, and don't retry.

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
infisical org list
```

It prints a table with `CURRENT`, `NAME`, `SLUG`, and `ID` columns. The org the CLI is using is
marked with `*` in the `CURRENT` column, and sub-organizations are listed under their parent with a
`└─` prefix. If there's more than one org, confirm with the user which one the project belongs in.
To change it:

```bash
infisical org switch <org>
```

`<org>` can be the org's name, slug, or `id`. Always pass it: without it, `org switch` opens an
interactive picker. If the org requires MFA, the command prompts for a code, so ask the user to run
it in their own terminal.

If the user is on a self-hosted instance and sees no sign-up option, their admin has disabled
sign-up. They need an invite from their admin.

## Step 2: Link the directory to a project

The link lives in `.infisical.yaml`. Older CLIs wrote `.infisical.json` instead, which the CLI still
reads when there's no `.infisical.yaml`.

If either file already exists in the directory, it's already linked, but check it's linked to the
right project before you import anything into it. First see which project commands here use:

```bash
infisical profile current
```

Besides the profile and org, it prints `Project:` (the project ID), `Project via:` (where the ID came
from), and the `Environment:` and `Secret path:` that commands without `--env` or `--path` use, each
with its own `via:` line. Each `via:` line ends with a hint such as `(override with --env)`, so match
on how the line starts, not the whole line.

- **`Project: unknown`**: the config file (path on the `Project config:` line) exists but can't be
  parsed. Commands that need a project stop with `project_config_invalid`. Tell the user and ask
  whether to fix the file or relink it as described below.
- **`Project: none`**: nothing links this directory after all. Continue with "Otherwise, create a
  project" below.
- **`Project via:` starts with `INFISICAL_PROJECT_ID environment variable`**: that variable overrides
  the file in this shell. Tell the user, since it's probably not the project the directory is linked to.

Then look the project up by that ID:

```bash
infisical secrets-manager projects get <project-id> -o json
```

**Pass the ID.** Without an argument, `projects get` lists every project in the org instead. It
doesn't read `.infisical.yaml`.

1. If it fails, read the error `code`:
   - `project_not_found`: the project doesn't exist in your org, or you aren't a member of it. The
     link is stale, or belongs to an instance you're not logged into
   - `auth_required`: the session expired. Go back to step 1
   - `project_type_not_supported`: the ID belongs to another product's project
   - **No `code`**: stderr is plain text with `Response Code: 403 Forbidden` and
     `This project does not belong to your selected organization`. The project exists, but in
     another org: check `infisical org list`

   In every case except `auth_required`, tell the user and ask whether to relink, or to switch org
   (`infisical org switch <org>`) or domain.
2. If it succeeds, tell the user the project's `name` and confirm that's where they want the secrets.

**`init` won't relink a directory without a terminal.** If the directory is already linked, it exits
with an error instead of overwriting the file. Only relink if the user asks you to: change
`project-id` under `secrets-management` in `.infisical.yaml` to the new project's `id`, keeping
the rest of the file. If the directory only has a legacy `.infisical.json`, change its `workspaceId`
instead. The file holds no secrets, so it's safe to read and edit.

Then skip to step 3.

Otherwise, create a project and link it:

```bash
infisical secrets-manager projects create --name <project-name> -o json
infisical init --project-id <id>
```

- Name the project after the repository directory unless the user asked for another name
- `projects create -o json` prints the new project, including `id`, `name`, `slug`, `orgId`, and
  its `environments` (`dev`, `staging`, and `prod` by default)
- `--project-id` skips the interactive org and project pickers; without it, `init` opens them

To link an existing project instead of creating one, list the org's projects with
`infisical secrets-manager projects get -o json`, confirm the right one with the user, then run
`infisical init --project-id <id>`. (`projects list` still works but is hidden from help.)

`init --project-id` writes a `.infisical.yaml` with only `project-id` under `secrets-management`.
That section can also hold `default-environment` and `mappings.git-branch-to-environment`
(auto-selects an environment from the current git branch), which `infisical run` and
`infisical secrets-manager secrets create` use when you don't pass `--env`, plus
`default-secret-path`. It holds no
secrets, so it's safe to commit.

## Step 3: Import existing `.env` files

**Don't open, read, or print the user's `.env` files.** They hold secret values. Let the CLI parse
them. Don't delete them either, unless the user asks you to (see step 5).

First check which of these files exist, by name only:

`.env` · `.env.local` · `.env.development` · `.env.staging` · `.env.production`

Leave out templates such as `.env.example` or `.env.sample`. They hold placeholders, not secrets.
If no files exist, skip to step 4.

### Pick an environment for each file

You upload each file separately with `infisical secrets-manager secrets create --file`, so each file
can go to its own environment. **Always pass `--env`.** Without it, `secrets create` uses the
`INFISICAL_ENVIRONMENT`
variable, then the environment mapped to the current git branch in `.infisical.yaml`, then its
`default-environment`, then `dev`. None of these is safe to rely on: a branch mapping such as
`main` → `prod` would send development values into production, and an existing project may have
no `dev`.

For a project you just created (its `environments` from `projects create -o json` are `dev`,
`staging`, and `prod`):

| File | `--env` |
|------|---------|
| `.env`, `.env.development`, `.env.local` | `dev` |
| `.env.staging` | `staging` |
| `.env.production` | `prod` |

For an existing project, list its environments with
`infisical secrets-manager environments get --projectId <project-id> -o json`, then ask the user
which slug each file goes to. Don't pick one from the branch mapping or `default-environment`, and
don't guess. If the environment they want doesn't exist, ask before creating it with
`infisical secrets-manager environments create <slug> --projectId <project-id>`. Confirm again
before sending anything to an environment that looks like production (`prod`, `production`).

**Files that share an environment can set the same key.** `create` never overwrites, so the second
file to set a key stops and you ask the user which value wins (see "When keys already exist"). Upload
the `dev` files in the order `.env`, `.env.development`, `.env.local`. Then, when the user agrees to
replace, the most specific file's value is the one that ends up in Infisical, the same way most
tools that load `.env` files layer them.

### Ask before uploading

Uploading sends secret values to a remote service, and `secrets create` doesn't ask for confirmation,
so the approval has to come from you. Tell the user which files you found, the project, and the
environment for each file, and wait for an explicit yes. Asking for "setup" or "the CLI" is not a
yes to uploading. If they decline, skip to step 4.

### Upload each file

Once they agree, run one command per file, in the order above:

```bash
infisical secrets-manager secrets create --file=<file> --env=<slug>
```

`create` only adds keys. If any key in the file already exists in that environment, it writes
nothing from the file and fails, so nothing already in Infisical is overwritten without the user
saying so. Don't use `infisical secrets set` instead: it silently overwrites.

- **Never add `-o`/`--output` or `--show-values`.** On success both print the secret values, and
  `-o json` prints them unmasked. The default table masks every value as `******`. Without `-o`,
  errors come back as text, which is enough here: they name the keys
- **Don't pass `--path` expecting a directory.** On `secrets create`, `--path` is the folder inside
  Infisical to write to, not a local directory. Leave it out to write to the root folder (`/`)
- **A `default-secret-path` in `.infisical.yaml` applies here.** Without `--path`, both
  `secrets create` and `infisical run` use the `INFISICAL_SECRET_PATH` variable, then
  `default-secret-path` (`defaultSecretPath` in a legacy `.infisical.json`), then `/`.
  `infisical profile current` prints the result as `Secret path:` and `Secret path via:`. If the
  `via:` line doesn't start with `default`, tell the user which folder the secrets will go to and
  confirm that's right. If it isn't, pass `--path=<folder>` on every upload (`create` and `update`)
  and on the `infisical run` command in step 4

On success the table lists every key in the file as `SECRET CREATED`. Report the key names to the
user, per file.

**If a file fails, nothing from that file is uploaded.** The CLI checks the whole file, and the
keys already in Infisical, before writing anything.

#### When keys already exist

```
Secrets "API_KEY", "DB_URL" already exist. Nothing was written.
```

The message lists **every** key in the file that already exists in that environment (one key reads
`Secret "API_KEY" already exists.`). For each key, work out where it came from: an earlier file in
this run that went to the same environment (its table lists the key), or a value that was already in
Infisical before you started. Tell the user the keys and where each came from, and ask whether this
file's values should replace them. Don't decide for them, even when layering suggests the answer.
The error also suggests `secrets update <KEY>=<value>`. Don't follow it: you don't have the value,
and the file is what holds it.

- **No:** skip the file. None of its keys are uploaded, including the new ones. The user can remove
  those lines from the file and ask you to upload it again, or add the values in the dashboard
- **Yes:** replace them with:

  ```bash
  infisical secrets-manager secrets update --file=<file> --env=<slug>
  ```

  `update` only changes keys that exist, and it succeeds only if **every** key in the file already
  exists. Its table shows `SECRET VALUE MODIFIED` (the key now has this file's value) or
  `SECRET VALUE UNCHANGED` (it already had this value). Tell the user which keys were modified,
  and for each one that came from an earlier file in this run, that the earlier file's value was
  replaced.

  If `update` fails with `Secrets "NEW_KEY", ... don't exist. Nothing was written.`, the file mixes
  keys that exist with keys that don't, and neither command can upload it as is. You now have both
  lists without opening the file: the existing keys from the `create` error, and the new keys from
  the `update` error. Tell the user. They can split the file themselves (for example, move the
  overriding keys into a separate file) and ask you to upload each part again, with `update` for the
  part that only has existing keys and `create` for the rest. Or they can add the values in the
  dashboard. Don't split or edit the file yourself

#### Other errors

- `Secret "<KEY>" is given more than once: pass each secret once`: the file defines the same key
  twice. Ask the user which line to keep and to remove the other, then upload the file again. Don't
  edit the file yourself
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
infisical secrets-manager secrets create --file=<file> --env=<slug>
```

In Claude Code, the user can type
`! infisical secrets-manager secrets create --file=<file> --env=<slug>` so the command runs in the
session and you can read the table or the error. The same applies to an `update` the user approved. In other agents, ask the user to run the
commands in their terminal and paste the tables back. Then continue with the checks above.

## Step 4: Run the app with secrets

Find the command the user starts the app with (`package.json` scripts, `Makefile`, `Procfile`, or
equivalent) and give them the wrapped version. Without `--env`, `run` picks the environment the same
way `secrets create` does in step 3: `INFISICAL_ENVIRONMENT`, then the branch mapping in
`.infisical.yaml`, then its `default-environment`, then `dev`. Whether to pass `--env` depends on
what happened in step 3:

- **You imported a development file** (`.env`, `.env.development`, or `.env.local`): pass the slug
  those files went to, even if it's `dev`. Otherwise the branch mapping or `default-environment` may
  pick a different environment from where the secrets went:

  ```bash
  infisical run --env=<slug> -- <start command>
  ```

- **You imported only `.env.staging` or `.env.production`:** no local development environment
  received secrets, so `dev` may be empty. Ask the user which environment to run against locally,
  and pass that slug with `--env`. Warn them if they pick production

- **No import** (no `.env` files, or the user declined): don't add `--env`. Leave the project's own
  selection in charge, so a branch mapping keeps working:

  ```bash
  infisical run -- <start command>
  ```

  If `.infisical.yaml` has no mapping or `default-environment`, this uses `dev`. For an existing
  project, check with the user that `dev` exists and is the right environment. If it isn't, pass
  the slug they give you

If you passed `--path` to the uploads, pass the same `--path` to `run`. If you relied on
`default-secret-path`, `run` picks it up too.

For example, `infisical run --env=dev -- npm run dev` after importing into `dev`. Mention that:

- `infisical secrets-manager secrets get` lists the project's secrets,
  `infisical secrets-manager secrets create KEY=value` adds one, and `secrets update KEY=value`
  changes one
- `--env <slug>` switches environments, e.g. `infisical run --env=staging -- npm start`
- They can view and edit everything in the Infisical dashboard

Don't run `infisical secrets` or `secrets-manager secrets get` yourself to "check" the import. It
prints secret values into your context. The `create` and `update` tables already tell you what was
uploaded.

## Step 5: Tell the user where their secrets are now

If you imported secrets, tell the user they now live in their Infisical project, and link to them:

```
<domain>/organizations/<orgId>/projects/secret-management/<projectId>/secrets/<env>
```

- `<domain>` is the session's `domain` from `infisical login status --json` (without a trailing
  `/api`). That covers both a fresh login and a reused session
- `<orgId>` and `<projectId>` are the `orgId` and `id` fields from `projects create -o json` (or
  `projects get <project-id> -o json`, if you linked an existing project)
- `<env>` is the environment you passed to `--env`. If files went to more than one environment, give
  a link for each

Then **strongly recommend deleting the imported `.env` files.** Infisical is now the source of
truth for those values, and `infisical run` injects them. A plaintext copy on disk is one more place
the secrets can leak from, and it drifts out of date as soon as someone changes a value in
Infisical.

Make the recommendation specific:

- Name only files that were uploaded in full: a `create` that succeeded, or an `update` the user
  approved that succeeded. If a file failed or was skipped, say so and don't recommend deleting it
- Don't recommend deleting a file whose keys a later file's `update` replaced in the same
  environment. Its value for those keys is no longer in Infisical, so the file may be the only copy.
  The user resolves the conflict first
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
