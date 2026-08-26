Here are both configs.

## GitHub — repository-environment scope

**Destination:** `github`

```json
{
  "destination": "github",
  "destinationConfig": {
    "scope": "repository-environment",
    "repository": {
      "owner": "<owner>",
      "name": "<repo>"
    },
    "environment": "<github-environment-name>"
  },
  "syncOptions": {
    "initialSyncBehavior": "overwrite-destination",
    "keySchema": "INFISICAL_{{secretKey}}",
    "disableSecretDeletion": false
  }
}
```

Note: `initialSyncBehavior` must be `overwrite-destination` since GitHub doesn't support importing secrets. The environment (e.g. `production`) must already exist in the repo's GitHub settings.

## Vercel — project scope

**Destination:** `vercel`

```json
{
  "destination": "vercel",
  "destinationConfig": {
    "scope": "project",
    "teamId": "<vercel-team-id>",
    "app": "<vercel-project-id>",
    "appName": "<vercel-project-name>",
    "env": "production",
    "sensitive": false
  },
  "syncOptions": {
    "initialSyncBehavior": "import-prioritize-destination",
    "keySchema": "INFISICAL_{{secretKey}}",
    "disableSecretDeletion": false
  }
}
```

`teamId` is required even though this is project scope, that's the most common misconfiguration here. I set `initialSyncBehavior` to `import-prioritize-destination` assuming you're migrating existing Vercel env vars into Infisical; if this is a fresh setup with no existing secrets to preserve, use `overwrite-destination` instead. Also keep in mind: if `sensitive` is `true`, Infisical can't read those values back on a later import, and Vercel's API never returns existing sensitive values during initial import regardless.
