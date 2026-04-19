# Setting Up a Vercel Secret Sync in Infisical Using the API

To automatically sync your Infisical secrets to Vercel, you need to complete two steps: create a Vercel Connection, then create the Vercel Sync. Here is a complete walkthrough.

---

## Step 1: Create a Vercel API Token

1. Go to your **Vercel Account Settings** and navigate to the **API Tokens** tab.
2. Create a new API Token with the appropriate scope for your projects.
3. Copy the token — you will need it in the next step.

---

## Step 2: Create a Vercel Connection in Infisical

Use the API to register your Vercel API token as a named connection in Infisical:

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/app-connections/vercel \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "my-vercel-connection",
    "projectId": "<your-infisical-project-id>",
    "method": "api-token",
    "credentials": {
      "apiToken": "<your-vercel-api-token>"
    }
  }'
```

Replace:
- `<your-infisical-project-id>` with your Infisical project ID
- `<your-vercel-api-token>` with the token you copied from Vercel

The response will include a `connectionId` — save this for the next step.

---

## Step 3: Create the Vercel Secret Sync

Use the API to create the sync, referencing the connection you just created:

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/secret-syncs/vercel \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "my-vercel-sync",
    "projectId": "<your-infisical-project-id>",
    "description": "Sync secrets from Infisical to Vercel",
    "connectionId": "<connection-id-from-step-2>",
    "environment": "dev",
    "secretPath": "/my-secrets",
    "isEnabled": true,
    "syncOptions": {
      "initialSyncBehavior": "overwrite-destination"
    },
    "destinationConfig": {
      "app": "<vercel-project-id>",
      "env": "preview",
      "branch": "main",
      "appName": "<your-vercel-project-name>",
      "teamId": "<your-vercel-team-id>"
    }
  }'
```

Replace the placeholder values:
- `<your-infisical-project-id>` — your Infisical project ID
- `<connection-id-from-step-2>` — the `connectionId` returned when you created the connection
- `<vercel-project-id>` — your Vercel project ID (starts with `prj_`)
- `<your-vercel-project-name>` — the display name of your Vercel project
- `<your-vercel-team-id>` — your Vercel team ID (starts with `team_`), if applicable

---

## Key Fields Explained

| Field | Description |
|---|---|
| `environment` | The Infisical environment to sync secrets from (e.g., `dev`, `staging`, `prod`) |
| `secretPath` | The path within the Infisical environment to sync (e.g., `/my-secrets`) |
| `isEnabled` | Set to `true` to enable automatic syncing when secrets change |
| `destinationConfig.env` | The Vercel environment to sync into: `production`, `preview`, or `development` |
| `destinationConfig.branch` | For preview environments, optionally scope secrets to a specific branch |

---

## Sync Options

The `initialSyncBehavior` field controls what happens on the first sync:

- **`overwrite-destination`** — Infisical secrets replace all existing Vercel environment variables.
- **`import-prefered-source`** — Conflicts are resolved in favor of Infisical values.
- **`import-prefered-destination`** — Conflicts are resolved in favor of existing Vercel values.

> **Note:** Vercel does not expose the values of sensitive (encrypted) environment variables. Because of this, Infisical cannot import those values during the initial sync — they will be overwritten if you use `overwrite-destination`.

---

## Additional Sync Options

- **Key Schema** — You can define a naming template for secret keys using `{{secretKey}}` and `{{environment}}` placeholders.
- **Auto-Sync** — When `isEnabled: true`, Infisical automatically pushes changes to Vercel whenever secrets are updated.
- **Disable Secret Deletion** — You can configure the sync to prevent Infisical from deleting secrets in Vercel if they are removed from Infisical.

---

Once the sync is created and enabled, any changes you make to secrets in the specified Infisical environment and path will automatically propagate to your Vercel project's environment variables.
