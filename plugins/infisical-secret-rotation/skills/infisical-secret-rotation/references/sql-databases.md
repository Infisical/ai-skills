# Rotation: SQL and NoSQL Databases

Covers `postgres-credentials`, `mysql-credentials`, `mssql-credentials`,
`oracledb-credentials`, `mongodb-credentials`, `redis-credentials`, and
`snowflake-user-key-pair`.

All of these except Snowflake share the same **SQL credentials** parameter shape and are
**dual-phase**.

## The two-user pattern (read this first)

This is the most common setup failure. Database rotations do **not** rotate one user's password
back and forth. They alternate between **two separate pre-existing accounts**:

```json
"parameters": {
  "username1": "infisical_app_a",
  "username2": "infisical_app_b"
}
```

Rules:

- **Both users must already exist in the database.** Infisical does not create them. Creating them is your job, before creating the rotation.
- **Both must have identical grants.** Whichever is active must be able to do everything your application needs. Mismatched grants produce an application that works for 30 days and then fails.
- Infisical rotates the password of the *inactive* user, promotes it to active, and leaves the previously active one valid until the following rotation. That overlap is what makes it zero-downtime.
- `secretsMapping.username` receives whichever user is currently active — so your application must read the **username** from Infisical too, not hardcode it.

That last point catches people out. An app that hardcodes the username and reads only the password
will break on the first rotation, because the active username changed.

### Creating the two users

The provider template offers a `createUserStatement` as a starting point. Run it twice, once per
username. For PostgreSQL:

```sql
-- create user role
CREATE USER infisical_user WITH ENCRYPTED PASSWORD 'temporary_password';

-- grant database connection permissions
GRANT CONNECT ON DATABASE my_database TO infisical_user;

-- grant relevant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO infisical_user;
```

The initial password is throwaway — the first rotation replaces it. Narrow the grants from
`ALL PRIVILEGES` to what the application actually needs.

For Microsoft SQL Server the login and the database user are separate objects:

```sql
-- Create login at the server level
CREATE LOGIN [infisical_user] WITH PASSWORD = 'my-password';

-- Grant server-level connect permission
GRANT CONNECT SQL TO [infisical_user];

-- Switch to the database where you want to create the user
USE my_database;

-- Create the database user mapped to the login
CREATE USER [infisical_user] FOR LOGIN [infisical_user];
```

## Parameters

| Field | Required | Description |
|-------|----------|-------------|
| `username1` | Yes | First login to rotate. **Must already exist.** |
| `username2` | Yes | Second login to rotate. **Must already exist.** |
| `rotationStatement` | No | SQL template used to change the password. Defaults per provider |
| `passwordRequirements` | No | Shape of the generated password |

### rotationStatement

A handlebars-style template. Only three expressions are permitted: `{{username}}`,
`{{password}}`, and `{{database}}`. The statement **must** contain both `{{username}}` and
`{{password}}` or validation rejects it.

Provider defaults:

| Provider | Default `rotationStatement` |
|----------|----------------------------|
| PostgreSQL | `ALTER USER "{{username}}" WITH PASSWORD '{{password}}'` |
| MySQL | `ALTER USER '{{username}}'@'%' IDENTIFIED BY '{{password}}'` |
| OracleDB | `ALTER USER "{{username}}" IDENTIFIED BY "{{password}}"` |
| MSSQL | Provider default (ALTER LOGIN form) |

Note the quoting differs by engine — PostgreSQL and Oracle use double quotes for the identifier,
MySQL uses single quotes plus a host part. Customize only if you need something beyond a password
change; otherwise take the default.

### passwordRequirements

```json
"passwordRequirements": {
  "length": 32,
  "required": { "digits": 2, "lowercase": 2, "uppercase": 2, "symbols": 2 },
  "allowedSymbols": "!@#$%^&*"
}
```

- `length` — 1 to 250
- `required.*` — minimum count of each class, each non-negative
- `allowedSymbols` — optional; restrict which symbols may appear

Use `allowedSymbols` when the database or a connection-string parser chokes on certain characters.
A password containing `@` or `/` inside a URI-style connection string is a classic breakage.

## secretsMapping

```json
"secretsMapping": {
  "username": "DB_USERNAME",
  "password": "DB_PASSWORD"
}
```

Both fields are required. `username` receives the currently active username, `password` the
generated password.

Provider default mapping names:

| Provider | Default username secret | Default password secret |
|----------|------------------------|------------------------|
| PostgreSQL | `POSTGRES_DB_USERNAME` | `POSTGRES_DB_PASSWORD` |
| MySQL | `MYSQL_USERNAME` | `MYSQL_PASSWORD` |
| OracleDB | `ORACLEDB_USERNAME` | `ORACLEDB_PASSWORD` |
| MongoDB | `MONGODB_DB_USERNAME` | `MONGODB_DB_PASSWORD` |
| Redis | `REDIS_USERNAME` | `REDIS_PASSWORD` |

## Full example — PostgreSQL

```bash
curl -X POST 'https://us.infisical.com/api/v2/secret-rotations/postgres-credentials' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-postgres-app",
    "projectId": "<project-id>",
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
        "required": { "digits": 2, "lowercase": 2, "uppercase": 2, "symbols": 0 }
      }
    },
    "secretsMapping": {
      "username": "DB_USERNAME",
      "password": "DB_PASSWORD"
    }
  }'
```

Then have the application read both `DB_USERNAME` and `DB_PASSWORD` from
`/database` in the `prod` environment.

## Redis specifics

Redis rotation manages ACL user passwords. The two users must exist as Redis ACL users with
matching permissions. Redis 6+ is required for ACL support.

## MongoDB specifics

MongoDB rotation manages database users through MongoDB's user management commands. Both users
need identical roles on the target database.

## Snowflake User Key Pair

`snowflake-user-key-pair` is different from the password rotations above — it rotates an RSA
**key pair** rather than a password, using Snowflake's support for two simultaneously registered
public keys (`RSA_PUBLIC_KEY` and `RSA_PUBLIC_KEY_2`). That is what makes it dual-phase.

The mapped secrets carry the private key material rather than a username/password pair. The
Snowflake user must exist and be configured for key-pair authentication.

## Gotchas

- **Both users must pre-exist with identical grants.** Repeated because it is the top failure.
- **Read the username from Infisical, not from config.** The active username alternates.
- Connection-string builders must URL-encode the password, or restrict `allowedSymbols`.
- A credential is revoked two intervals after it was issued. Application secret caches must be well under 2× `rotationInterval`.
- Managed databases sometimes restrict `ALTER USER`. Verify the App Connection's user can change other users' passwords before creating the rotation.
