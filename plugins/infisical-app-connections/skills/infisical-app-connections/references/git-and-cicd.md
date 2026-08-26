# App Connections: Git Hosts and CI/CD

## GitHub — `github`

Three methods: `github-app`, `oauth`, `pat`. **Prefer `github-app`.**

All three support GitHub Cloud and GitHub Enterprise Server via `instanceType`:

| Field | Values | Notes |
|-------|--------|-------|
| `instanceType` | `cloud` (default) or `server` | Omit for github.com |
| `host` | hostname | **Required when `instanceType` is `server`**, optional otherwise |

If you set `instanceType: "server"` without `host`, validation fails with
`Host is required for server instance type`.

### `github-app` (recommended)

```json
{
  "name": "prod-github",
  "method": "github-app",
  "credentials": {
    "code": "<code from the GitHub App install redirect>",
    "installationId": "<GitHub App installation id>"
  }
}
```

| Credential field | Required | Notes |
|------------------|----------|-------|
| `code` | Yes | From the App installation redirect |
| `installationId` | Yes | The installation, not the App id |
| `gitHubAppId` | No | UUID of the Infisical-side GitHub App record, for self-hosted instances running their own App |
| `instanceType` / `host` | See above | |

Why prefer it: installation tokens are short-lived and automatically refreshed, permissions are
scoped per-repository at install time, and it survives the departure of whoever set it up. A PAT
belongs to a person and dies with their account.

Self-hosted Infisical needs its own GitHub App registered; `gitHubAppId` selects it.

### `oauth`

```json
{
  "method": "oauth",
  "credentials": { "code": "<oauth code>" }
}
```

Interactive browser flow — inconvenient to automate. Acts on behalf of the authorizing user.

### `pat`

```json
{
  "method": "pat",
  "credentials": { "personalAccessToken": "ghp_..." }
}
```

Note the field name is `personalAccessToken`, not `pat` or `token`. The method is `pat`; the field
is spelled out.

Last resort. Tied to a human account, broad by default, and needs manual rotation.

### Permissions

| Consumer | Needs |
|----------|-------|
| GitHub secret sync (repository scope) | Repository **Secrets: write** |
| GitHub secret sync (organization scope) | Organization **Secrets: write** |
| GitHub secret sync (repository-environment scope) | Repository **Environments** access plus Secrets: write |
| GitHub Radar scanning | Repository **contents: read** and webhook access |

GitHub secrets are write-only — Infisical can set them but never read them back. That is why the
GitHub sync supports only `overwrite-destination` and no import. See `infisical-secret-syncs`.

## GitHub Radar — `github-radar`

A **separate connection type** from `github`, used only by Secret Scanning. Method: `github-app`.

```json
{
  "name": "scanning-radar",
  "method": "github-app",
  "credentials": {
    "code": "<GitHub Radar App code>",
    "installationId": "<installation id>"
  }
}
```

Do not use a `github` connection for scanning data sources, or a `github-radar` connection for
secret syncs. They install different GitHub Apps with different permissions — Radar needs to read
repository contents and receive push webhooks, which a sync App has no reason to hold.

## GitLab — `gitlab`

Methods: `oauth`, `access-token`. Both support self-managed GitLab.

### `access-token`

```json
{
  "method": "access-token",
  "credentials": {
    "accessToken": "glpat-...",
    "instanceUrl": "https://gitlab.self-managed.example.com"
  }
}
```

| Credential field | Required | Notes |
|------------------|----------|-------|
| `accessToken` | Yes | Project, group, or personal access token |
| `instanceUrl` | No | Must be a valid URL. Omit for gitlab.com |

### `oauth`

```json
{
  "method": "oauth",
  "credentials": {
    "code": "<oauth code>",
    "instanceUrl": "https://gitlab.self-managed.example.com"
  }
}
```

For the GitLab sync, the token needs `api` scope to manage CI/CD variables. A group token covers
group-scope syncs; a project token covers project-scope only.

## Bitbucket — `bitbucket`

Method: `api-token`.

Bitbucket needs an **App Password** or API token with repository admin rights to manage repository
variables. Workspace and repository are configured on the sync, not the connection.

## Azure DevOps — `azure-devops`

Credentials are supplied directly rather than through a discrete method enum. Needs a PAT with
variable-group management permission. Check
`docs/integrations/app-connections/azure-devops` for the current field list.

Do not confuse this with the other five Azure connections — see `references/cloud-providers.md`.

## CI providers

| Connection | Slug | Method | Notes |
|------------|------|--------|-------|
| CircleCI | `circleci` | `api-token` | Personal API token |
| Travis CI | `travis-ci` | `api-token` | |
| TeamCity | `teamcity` | `access-token` | |
| Octopus Deploy | `octopus-deploy` | `api-key` | |
| Spacelift | `spacelift` | `api-key-secret` | Key **ID plus secret**, not a single token |
| Rundeck | `rundeck` | `api-token` | |
| Terraform Cloud | `terraform-cloud` | `api-token` | Team or user token |

Spacelift's `api-key-secret` is the odd one — it takes two values where the others take one.

## Choosing between them

| The user says... | Connection + method |
|------------------|--------------------|
| "push secrets to GitHub Actions" | `github` + `github-app` |
| "scan our GitHub repos for leaked secrets" | `github-radar` + `github-app` |
| "we run GitHub Enterprise Server" | `github`, `instanceType: "server"`, `host` set |
| "push to GitLab CI variables" | `gitlab` + `access-token`, `api` scope |
| "self-managed GitLab" | `gitlab` with `instanceUrl` |
| "our CI is CircleCI" | `circleci` + `api-token` |
| "Terraform Cloud workspace variables" | `terraform-cloud` + `api-token` |
