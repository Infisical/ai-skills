# Setting Up a Vercel Secret Sync in Infisical via API

This guide walks you through syncing Infisical secrets to Vercel automatically using the Infisical API.

## Overview

Infisical's Secret Sync feature lets you push secrets from an Infisical project environment to external destinations like Vercel. You'll need:

1. An Infisical project with secrets
2. A Vercel API token
3. The Vercel project and team details you want to sync to

---

## Step 1: Create a Vercel Sync Integration (App Connection)

Before creating a sync, you need to register a Vercel connection (app connection) in Infisical that holds your Vercel credentials.

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/app-connections \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "my-vercel-connection",
    "app": "vercel",
    "method": "api-token",
    "credentials": {
      "apiToken": "<YOUR_VERCEL_API_TOKEN>"
    }
  }'
```

**Response** will include an `id` for the connection — save this as `<APP_CONNECTION_ID>`.

---

## Step 2: List Available Vercel Projects (Optional)

To confirm your connection works and find the correct Vercel project/team IDs:

```bash
curl --request GET \
  --url 'https://app.infisical.com/api/v1/app-connections/<APP_CONNECTION_ID>/available-sync-options' \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>'
```

This returns the Vercel projects and teams accessible via the token.

---

## Step 3: Create the Secret Sync

Now create the actual sync that maps an Infisical project environment to a Vercel project.

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/secret-syncs/vercel \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "my-vercel-sync",
    "projectId": "<INFISICAL_PROJECT_ID>",
    "environment": "prod",
    "secretPath": "/",
    "connectionId": "<APP_CONNECTION_ID>",
    "destinationConfig": {
      "app": "<VERCEL_PROJECT_NAME_OR_ID>",
      "appId": "<VERCEL_PROJECT_ID>",
      "teamId": "<VERCEL_TEAM_ID>",
      "targetEnvironment": "production"
    },
    "syncOptions": {
      "initialSyncBehavior": "overwrite-destination",
      "autoSyncEnabled": true
    }
  }'
```

### Key fields

| Field | Description |
|---|---|
| `projectId` | Your Infisical project ID |
| `environment` | Infisical environment slug (e.g. `prod`, `staging`, `dev`) |
| `secretPath` | Folder path in Infisical to sync from (use `/` for root) |
| `connectionId` | The app connection ID from Step 1 |
| `destinationConfig.app` | Vercel project name |
| `destinationConfig.appId` | Vercel project ID |
| `destinationConfig.teamId` | Vercel team ID (omit for personal accounts) |
| `destinationConfig.targetEnvironment` | Vercel environment: `production`, `preview`, or `development` |
| `syncOptions.initialSyncBehavior` | `overwrite-destination` replaces all existing Vercel env vars; use `prefer-destination` to keep existing values |
| `syncOptions.autoSyncEnabled` | If `true`, secrets sync automatically when changed in Infisical |

The response will include the sync `id` — save it as `<SYNC_ID>`.

---

## Step 4: Trigger a Manual Sync

To immediately push secrets to Vercel without waiting for an automatic trigger:

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/secret-syncs/vercel/<SYNC_ID>/sync \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>'
```

---

## Step 5: Check Sync Status

```bash
curl --request GET \
  --url https://app.infisical.com/api/v1/secret-syncs/vercel/<SYNC_ID> \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>'
```

Look at the `lastSyncedAt` and `status` fields in the response to confirm the sync succeeded.

---

## Step 6: List All Secret Syncs (Optional)

```bash
curl --request GET \
  --url 'https://app.infisical.com/api/v1/secret-syncs?projectId=<INFISICAL_PROJECT_ID>' \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>'
```

---

## Step 7: Delete a Sync (Optional)

If you want to remove the sync (and optionally clean up secrets in Vercel):

```bash
curl --request DELETE \
  --url 'https://app.infisical.com/api/v1/secret-syncs/vercel/<SYNC_ID>?removeSecrets=false' \
  --header 'Authorization: Bearer <INFISICAL_TOKEN>'
```

Set `removeSecrets=true` to also delete the synced environment variables from Vercel.

---

## Authentication

All API calls require a valid Infisical token in the `Authorization: Bearer` header. You can use:

- A **machine identity access token** (recommended for automation)
- A **user JWT** (for manual/testing use)

To get a machine identity token:

```bash
curl --request POST \
  --url https://app.infisical.com/api/v1/auth/universal-auth/login \
  --header 'Content-Type: application/json' \
  --data '{
    "clientId": "<MACHINE_IDENTITY_CLIENT_ID>",
    "clientSecret": "<MACHINE_IDENTITY_CLIENT_SECRET>"
  }'
```

Use the returned `accessToken` as your `<INFISICAL_TOKEN>`.

---

## Notes

- Vercel environment variables synced by Infisical are marked with the source so you can distinguish them from manually set vars.
- If `autoSyncEnabled` is `true`, any secret change in the configured Infisical path will automatically trigger a push to Vercel.
- For self-hosted Infisical, replace `https://app.infisical.com` with your instance URL throughout.
