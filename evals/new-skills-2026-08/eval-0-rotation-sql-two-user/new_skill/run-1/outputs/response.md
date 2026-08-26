Setting up a PostgreSQL rotation for a production app user with a 30-day interval. Here's the request body and the database prep required beforehand.

## Database prep (do this first)

Postgres rotation is **dual-phase** and needs two pre-existing users with identical grants. Infisical never creates users, it only alternates passwords between them.

```sql
-- User 1
CREATE USER infisical_app_a WITH ENCRYPTED PASSWORD 'temporary_password_1';
GRANT CONNECT ON DATABASE my_database TO infisical_app_a;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO infisical_app_a;

-- User 2 (identical grants)
CREATE USER infisical_app_b WITH ENCRYPTED PASSWORD 'temporary_password_2';
GRANT CONNECT ON DATABASE my_database TO infisical_app_b;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO infisical_app_b;
```

Narrow `ALL PRIVILEGES` down to whatever your app actually needs, not more. The temporary passwords don't matter, the first rotation replaces them.

Also confirm before creating the rotation:

- A **PostgreSQL App Connection** already exists in Infisical, and the credentials behind it have permission to run `ALTER USER ... WITH PASSWORD` on both accounts (some managed Postgres providers restrict this).
- Your application reads **both** `DB_USERNAME` and `DB_PASSWORD` from Infisical at runtime, not just the password. The active username flips between the two accounts on every rotation, so a hardcoded username breaks on the first rotation.

## API request body

```json
{
  "name": "prod-postgres-app",
  "projectId": "<project-id>",
  "description": "Rotates the production app DB user",
  "connectionId": "<postgres-app-connection-uuid>",
  "environment": "prod",
  "secretPath": "/database",
  "isAutoRotationEnabled": true,
  "rotationInterval": 30,
  "rotateAtUtc": { "hours": 3, "minutes": 0 },
  "parameters": {
    "username1": "infisical_app_a",
    "username2": "infisical_app_b",
    "passwordRequirements": {
      "length": 32,
      "required": { "digits": 2, "lowercase": 2, "uppercase": 2, "symbols": 2 },
      "allowedSymbols": "!@#$%^&*"
    }
  },
  "secretsMapping": {
    "username": "DB_USERNAME",
    "password": "DB_PASSWORD"
  }
}
```

```bash
curl -X POST 'https://us.infisical.com/api/v2/secret-rotations/postgres-credentials' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ ... body above ... }'
```

Notes on the choices made here:

- `connectionId` must point to a `postgres`-type App Connection, fill in the UUID.
- `rotateAtUtc` at 03:00 UTC is just a low-traffic default, adjust to your actual quiet window.
- `allowedSymbols` is restricted to a safe set so the generated password won't break a URI-style connection string if you're constructing one manually (`@` and `/` are classic breakers). If your app already URL-encodes secret values, you can drop this.
- This is dual-phase: a credential is revoked two intervals later (60 days), so keep any secret cache TTL in the app well under that.

Fill in `projectId` and `connectionId` and this is ready to send. Want me to also cover how to wire the app (Agent, Kubernetes Operator, or SDK) to pick up the rotated value automatically?
