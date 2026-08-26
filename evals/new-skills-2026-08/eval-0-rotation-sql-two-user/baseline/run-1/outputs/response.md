I don't have web access in this session to pull Infisical's live OpenAPI spec, so I can't verify the exact field names against current docs before giving you this. What's below is accurate to my knowledge of Infisical's Secret Rotation v2 API (the Postgres credentials rotation type), but since you're at Infisical, I'd sanity-check field names against `/docs/api-reference` or the Zod schema in the backend before you run this against prod.

## How it works

Postgres rotation uses a **dual-user, zero-downtime strategy**: you give it two pre-created DB usernames with identical grants. Each cycle, Infisical rotates the password on whichever user is currently *inactive*, then flips the "active" user and writes its new username/password into the mapped secrets. The app never sees a window where its current credential is invalid.

## What to prepare in Postgres first

1. **Two identical application users**, e.g. `app_user_1` and `app_user_2`
   - Same role memberships, same GRANTs on schemas/tables/sequences the app needs
   - Both able to log in (`LOGIN` attribute), both already have working passwords you're about to hand off to Infisical

2. **A manager/rotator account** Infisical will use to connect and run `ALTER ROLE ... WITH PASSWORD ...` against those two users
   - Needs `CREATEROLE` (or superuser) so it can change passwords on `app_user_1`/`app_user_2`
   - This does not need to be one of the two app users, and shouldn't be

3. **Network reachability** from wherever Infisical connects
   - Infisical Cloud: allowlist Infisical's egress IPs, or put a self-hosted Gateway in front of the DB if it's in a private VPC
   - Self-hosted Infisical: make sure the instance can route to the Postgres host/port

4. **SSL/TLS mode** matching what your production Postgres enforces (`require`/`verify-full`), plus the CA cert if it's self-signed, since you'll need this for the App Connection config

5. **Create the Postgres App Connection in Infisical first** (separate resource, done via UI or `POST /api/v1/app-connections/postgres`), using the manager account from step 2. The rotation body below just references its `connectionId`, it doesn't take raw DB credentials directly.

## Rotation creation request

`POST /api/v2/secret-rotations/postgres-credentials`

```json
{
  "name": "prod-postgres-app-user-rotation",
  "description": "Rotates the production app's PostgreSQL credentials every 30 days",
  "projectId": "<your-project-id>",
  "environment": "prod",
  "secretPath": "/",
  "connectionId": "<app-connection-id-for-the-manager-account>",
  "isAutoRotationEnabled": true,
  "rotationInterval": 30,
  "rotateAtUtc": {
    "hours": 3,
    "minutes": 0
  },
  "parameters": {
    "username1": "app_user_1",
    "username2": "app_user_2"
  },
  "secretsMapping": {
    "username": "POSTGRES_USERNAME",
    "password": "POSTGRES_PASSWORD"
  }
}
```

Field notes:
- `secretPath` / `environment` is where the rotated `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` secrets land, that's what your app should read
- `rotationInterval: 30` is days between rotations
- `parameters.username1`/`username2` are the two DB users from step 1, exactly as they exist in Postgres
- `secretsMapping` lets you rename the output secret keys to whatever your app expects

Before you run this for real, I'd grep the backend repo for the actual Zod schema on the `postgres-credentials` rotation route (or check the request preview in the dashboard when you build one there by hand) since I can't confirm these field names live right now.
