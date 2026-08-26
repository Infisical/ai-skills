Here are the two sync configs. I don't have live access to fetch Infisical's OpenAPI spec in this session, so I've marked the parts that are enum values verbatim from the skill (high confidence) versus JSON key names I'm inferring from Infisical's general sync API shape (worth a quick sanity-check against your instance's API reference before running).

## 1. GitHub — repository environment scope

`POST /api/v1/secret-syncs/github`

```json
{
  "name": "github-env-sync",
  "projectId": "<project-id>",
  "connectionId": "<github-app-connection-id>",
  "environment": "prod",
  "secretPath": "/",
  "isAutoSyncEnabled": true,
  "destinationConfig": {
    "scope": "environment",
    "repo": "owner/repo-name",
    "env": "production"
  },
  "syncOptions": {
    "initialSyncBehavior": "overwrite-destination",
    "keySchema": "INFISICAL_{{secretKey}}",
    "disableSecretDeletion": false
  }
}
```

- `destinationConfig.scope` enum (skill-confirmed): `organization`, `repository`, `environment` — use `environment` here.
- `syncOptions.initialSyncBehavior` (skill-confirmed): GitHub supports **only** `overwrite-destination`. It does not support import, so this is the only legal value.
- The GitHub `environment` (e.g. `production`) must already exist in the repo's settings before you create the sync.

## 2. Vercel — project sync

`POST /api/v1/secret-syncs/vercel`

```json
{
  "name": "vercel-prod-sync",
  "projectId": "<infisical-project-id>",
  "connectionId": "<vercel-app-connection-id>",
  "environment": "prod",
  "secretPath": "/",
  "isAutoSyncEnabled": true,
  "destinationConfig": {
    "app": "<vercel-project-id>",
    "env": "production",
    "branch": ""
  },
  "syncOptions": {
    "initialSyncBehavior": "import-prioritize-infisical",
    "keySchema": "INFISICAL_{{secretKey}}",
    "disableSecretDeletion": false
  }
}
```

- `syncOptions.initialSyncBehavior` (skill-confirmed enum): `overwrite-destination`, `import-prioritize-infisical`, or `import-prioritize-vercel`. Since Vercel supports import, prefer one of the import options if you already have secrets in Vercel you don't want clobbered on the first run.
- `destinationConfig.env` is Vercel's target environment: `production`, `preview`, or `development`.
- `destinationConfig.branch` is only meaningful when `env` is `preview` — leave it empty/omit otherwise.
- Gotcha from the skill: Vercel's API doesn't return values for sensitive env vars on import, so any Vercel secret marked sensitive will land in Infisical with an empty value after the first sync. You'll need to re-enter those manually in Infisical.

**One flag before you run these:** the top-level field names I used (`connectionId`, `secretPath`, `isAutoSyncEnabled`, `destinationConfig.app`, `destinationConfig.scope`, etc.) reflect Infisical's general secret-sync API conventions, but the skill documents UI field labels rather than raw JSON keys, and I couldn't hit the live API reference to confirm exact casing in this session. Worth a quick diff against a `GET` on an existing sync (or the OpenAPI schema) before wiring these into a script, just so a typo'd key doesn't silently get ignored by the API.
