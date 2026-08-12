A quick caveat up front: I don't have live internet or file-system access in this session, so this is from training-time knowledge of Infisical's Secret Sync API rather than a live doc fetch. The overall shape (fields, nesting) I'm confident in since it's consistent across every Infisical sync integration; the destination-specific key names (`app` vs `projectId`, `env` vs `environment`) are the part I'd double check against your instance's OpenAPI spec (`GET /api/docs`) or the Zod schemas in `backend/src/services/secret-sync/{github,vercel}/` before shipping, since I can't fetch either right now.

Both syncs require an existing App Connection (`connectionId`) for GitHub and Vercel respectively, created beforehand via the App Connections API.

## Shared shape

Every secret sync (`POST /api/v1/secret-syncs/{app}`) shares this envelope:

```jsonc
{
  "name": "string",
  "projectId": "string",
  "description": "string",           // optional
  "connectionId": "string",          // the App Connection ID
  "environment": "string",           // Infisical source environment slug, e.g. "prod"
  "secretPath": "/",
  "isEnabled": true,
  "syncOptions": {
    "initialSyncBehavior": "overwrite-destination" | "import-prioritize-source" | "import-prioritize-destination",
    "disableSecretDeletion": false,
    "keySchema": "{{secretKey}}"     // optional rename template
  },
  "destinationConfig": { /* per-integration, see below */ }
}
```

`initialSyncBehavior` enum (`SecretSyncInitialSyncBehavior`) — same three values across every integration:
- `overwrite-destination` — wipe destination, replace with source secrets
- `import-prioritize-source` — merge in, source wins on key conflicts
- `import-prioritize-destination` — merge in, destination wins on key conflicts

## GitHub → repository environment secrets

`POST /api/v1/secret-syncs/github`

```jsonc
{
  "name": "github-prod-env-sync",
  "projectId": "<infisical-project-id>",
  "connectionId": "<github-app-connection-id>",
  "environment": "prod",
  "secretPath": "/",
  "isEnabled": true,
  "syncOptions": {
    "initialSyncBehavior": "overwrite-destination",
    "disableSecretDeletion": false
  },
  "destinationConfig": {
    "scope": "repository-environment",
    "org": "my-github-org",
    "repo": "my-repo",
    "env": "production"
  }
}
```

`destinationConfig.scope` enum (`GitHubSyncScope`) — GitHub sync supports three scopes, environment is one of them:
- `organization` — pairs with `org`, and `visibility` (`all` | `private` | `selected`, plus `selectedRepositoryIds` when `selected`)
- `repository` — pairs with `org`, `repo`
- `repository-environment` — pairs with `org`, `repo`, `env` (the GitHub environment name, e.g. `production`)

## Vercel → project environment variables

`POST /api/v1/secret-syncs/vercel`

```jsonc
{
  "name": "vercel-prod-sync",
  "projectId": "<infisical-project-id>",
  "connectionId": "<vercel-connection-id>",
  "environment": "prod",
  "secretPath": "/",
  "isEnabled": true,
  "syncOptions": {
    "initialSyncBehavior": "overwrite-destination",
    "disableSecretDeletion": false
  },
  "destinationConfig": {
    "app": "<vercel-project-id>",
    "appName": "my-vercel-app",
    "env": "production",
    "teamId": "<vercel-team-id>"
  }
}
```

- `env` enum: `development` | `preview` | `production` — this is Vercel's own environment target, not the Infisical source `environment` field above.
- `teamId` is only needed if the Vercel App Connection authenticates against a team-scoped account.
- If you push to `preview` and want it scoped to a specific Git branch rather than all preview deployments, there's an optional preview-branch field on the Vercel side of this config, worth confirming the exact key for in the schema before use.

Given you're at Infisical, the fastest ground truth is the Zod schema files (`github-sync-schemas.ts`, `vercel-sync-schemas.ts`) or the live OpenAPI spec, since those will catch any drift from what I've recalled here.
