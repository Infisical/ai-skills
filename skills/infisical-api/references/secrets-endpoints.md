# Secrets Endpoints

All secret operations use `/api/v4/secrets`. Previous API versions (v1, v2, v3) are deprecated.

## List Secrets

### Endpoint

```
GET /api/v4/secrets
```

### Query Parameters

**This endpoint is not paginated.** It returns every secret at the requested path and accepts
no `offset` or `limit`.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| projectId | string | Yes | - | ID of the project |
| environment | string | Yes | - | Environment slug (e.g., "dev", "prod") |
| secretPath | string | No | "/" | Secret folder path (e.g., "/database", "/") |
| viewSecretValue | boolean | No | **true** | Return plaintext values; `false` hides them |
| expandSecretReferences | boolean | No | **true** | Expand secret references (e.g., `${OTHER_SECRET}`) |
| recursive | boolean | No | false | Include secrets from all subdirectories |
| includeImports | boolean | No | **true** | Include secrets from imported environments |
| includePersonalOverrides | boolean | No | false | Include personal secret overrides |
| tagSlugs | string | No | - | Comma-separated tag slugs to filter by |
| metadataFilter | string | No | - | `key=k1,value=v1\|key=k2,value=v2` — max 10 pairs |

Note `viewSecretValue`, `expandSecretReferences`, and `includeImports` default to **true**, not
false.

### Response

```json
{
  "secrets": [
    {
      "id": "secret-id-uuid",
      "_id": "secret-id-uuid",
      "version": 1,
      "workspace": "project-id",
      "environment": "dev",
      "secretPath": "/",
      "secretKey": "DATABASE_URL",
      "secretValue": "postgres://user:pass@localhost/db",
      "secretValueHidden": false,
      "secretComment": "Production database connection",
      "type": "shared",
      "skipMultilineEncoding": false,
      "secretMetadata": [],
      "tags": [
        {
          "id": "tag-id",
          "slug": "database",
          "name": "Database",
          "color": "#3b82f6"
        }
      ],
      "createdAt": "2026-04-16T10:30:00.000Z",
      "updatedAt": "2026-04-16T10:30:00.000Z"
    }
  ],
  "imports": [
    {
      "secretPath": "/shared",
      "environment": "dev",
      "secrets": []
    }
  ]
}
```

Key points on the shape:
- The secret's key field is **`secretKey`**, not `secretName`
- The project field is **`workspace`**; there is no `project` field
- There is no `total`, `offset`, `limit`, or `items` key
- `imports` is present when `includeImports` is on
- May return **304 Not Modified** with an empty body on a conditional request

### Example

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Include subfolders, hide values (key names only)
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&recursive=true&viewSecretValue=false' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Get Secret

### Endpoint

```
GET /api/v4/secrets/{secretName}
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| projectId | string | Yes | - | ID of the project |
| environment | string | Yes | - | Environment slug |
| secretPath | string | No | "/" | Secret folder path |
| type | string | No | `shared` | `shared` or `personal` |
| version | integer | No | - | Fetch a specific historical version |
| viewSecretValue | boolean | No | **true** | Return plaintext value; `false` hides it |
| expandSecretReferences | boolean | No | **true** | Expand `${OTHER_SECRET}` references |
| includeImports | boolean | No | **true** | Resolve the secret through imports if not found locally |

### Response

```json
{
  "secret": {
    "id": "secret-id-uuid",
    "_id": "secret-id-uuid",
    "version": 1,
    "workspace": "project-id",
    "environment": "dev",
    "secretPath": "/",
    "secretKey": "API_KEY",
    "secretValue": "sk_live_abc123def456ghi789",
    "secretValueHidden": false,
    "secretComment": "Third-party API key",
    "type": "shared",
    "skipMultilineEncoding": false,
    "createdAt": "2026-04-16T10:30:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z"
  }
}
```

### Example

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets/API_KEY?projectId=abc123&environment=dev&secretPath=/' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Create Secret

### Endpoint

```
POST /api/v4/secrets/{secretName}
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| projectId | string | Yes | ID of the project |
| environment | string | Yes | Environment slug |
| secretPath | string | No | Secret folder path (default: "/") |
| secretValue | string | Yes | The secret value (plaintext) |
| type | string | No | "shared" or "personal" (default: "shared") |
| tagIds | array | No | List of tag IDs to attach |
| secretComment | string | No | Comment/description for the secret (default: "") |
| secretMetadata | array | No | Key/value metadata pairs attached to the secret |

The secret's key comes from the `{secretName}` path segment, not the body.

### Response

```json
{
  "secret": {
    "id": "secret-id-uuid",
    "_id": "secret-id-uuid",
    "version": 1,
    "workspace": "project-id",
    "environment": "dev",
    "secretPath": "/",
    "secretKey": "NEW_SECRET",
    "secretValue": "super-secret-value",
    "secretComment": "My new secret",
    "type": "shared",
    "createdAt": "2026-04-16T10:30:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z"
  }
}
```

If the project has a secret approval policy covering this path, the response is instead
`{ "approval": { ... } }` and no secret is written until the request is approved. Handle both
shapes.

### Example

```bash
curl -X POST 'https://us.infisical.com/api/v4/secrets/DATABASE_PASSWORD' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secretValue": "my-secure-password",
    "type": "shared",
    "secretComment": "Database password for dev environment"
  }'
```

## Update Secret

### Endpoint

```
PATCH /api/v4/secrets/{secretName}
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| projectId | string | Yes | ID of the project |
| environment | string | Yes | Environment slug |
| secretPath | string | No | Secret folder path |
| secretValue | string | No | New secret value |
| secretComment | string | No | Updated comment/description |
| tagIds | array | No | Updated list of tag IDs |
| secretMetadata | array | No | Replacement key/value metadata pairs |
| newSecretName | string | No | Rename the secret |
| skipMultilineEncoding | boolean | No | Toggle multiline encoding |
| type | string | No | "shared" or "personal" (default: "shared") |

### Response

Same as Create Secret response — including the `{ "approval": { ... } }` variant when a secret
approval policy applies.

### Example

```bash
curl -X PATCH 'https://us.infisical.com/api/v4/secrets/DATABASE_PASSWORD' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secretValue": "new-secure-password"
  }'
```

Renaming a secret uses `newSecretName` while the path segment stays the current name:

```bash
curl -X PATCH 'https://us.infisical.com/api/v4/secrets/OLD_NAME' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "newSecretName": "NEW_NAME"
  }'
```

## Delete Secret

### Endpoint

```
DELETE /api/v4/secrets/{secretName}
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| projectId | string | Yes | ID of the project |
| environment | string | Yes | Environment slug |
| secretPath | string | No | Secret folder path (default: "/") |

### Response

```json
{
  "secret": {
    "id": "secret-id-uuid",
    "secretKey": "DELETED_SECRET",
    "workspace": "project-id",
    "environment": "dev",
    "version": 3,
    "type": "shared"
  }
}
```

### Example

```bash
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/OLD_SECRET?projectId=abc123&environment=dev&secretPath=/' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Batch Create / Update / Delete Secrets

### Endpoints

```
POST   /api/v4/secrets/batch
PATCH  /api/v4/secrets/batch
DELETE /api/v4/secrets/batch
```

All three take a `secrets` **array of objects**, keyed by `secretKey`. There is no `secretIds`
field.

### Batch create

```bash
curl -X POST 'https://us.infisical.com/api/v4/secrets/batch' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secrets": [
      { "secretKey": "SECRET_1", "secretValue": "value1", "secretComment": "first" },
      { "secretKey": "SECRET_2", "secretValue": "value2" }
    ]
  }'
```

Per-secret fields: `secretKey` (required), `secretValue` (required), `secretComment`,
`tagIds`, `secretMetadata`.

### Batch delete

Identify secrets by key, not ID:

```bash
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/batch' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secrets": [
      { "secretKey": "SECRET_1" },
      { "secretKey": "SECRET_2" }
    ]
  }'
```

### Response

```json
{
  "secrets": [
    { "id": "uuid1", "secretKey": "SECRET_1", "workspace": "project-id", "environment": "dev" },
    { "id": "uuid2", "secretKey": "SECRET_2", "workspace": "project-id", "environment": "dev" }
  ]
}
```

As with single-secret writes, a project with a secret approval policy returns
`{ "approval": { ... } }` instead.

## Other Secret Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v4/secrets/id/{secretId}` | Fetch a secret by its UUID instead of its key |
| `POST /api/v4/secrets/move` | Move secrets between folders or environments |
| `POST /api/v4/secrets/duplicate` | Copy secrets to another folder or environment |
| `GET /api/v4/secrets/{secretName}/secret-reference-tree` | Inspect what a secret's references resolve to |
| `GET /api/v4/secrets/{secretName}/reference-dependency-tree` | Inspect which secrets depend on this one |
| `POST /api/v4/secrets/backfill-secret-references` | Rebuild the reference index for a project |

## Important Notes

### API Version

- Use `/api/v4/secrets` for all new code
- `/api/v1/secrets`, `/api/v2/secrets`, and `/api/v3/secrets` are deprecated
- Migrate existing integrations to v4 endpoints

### Secret Names

- Must be unique within the environment and secret path
- Use uppercase with underscores (e.g., `DATABASE_PASSWORD`)
- Cannot contain spaces or special characters

### Secret Types

- **shared**: Visible to all project members with appropriate permissions
- **personal**: Only visible to the user who created it

### Secret Values

- Plaintext strings only
- For large values, base64-encode before creating
- References using `${SECRET_NAME}` syntax are supported when `expandSecretReferences=true`

### Tags

- Secrets can have multiple tags
- Tags are organization-wide but applied per secret
- Use `tagSlugs` parameter to filter list results by tag

### Pagination

- **There is no pagination on `/api/v4/secrets`.** `offset` and `limit` are not accepted and have
  no effect. The endpoint returns every secret at the requested path in one response.
- To reduce the result set, scope with `secretPath`, keep `recursive=false`, or filter with
  `tagSlugs` / `metadataFilter`.
- Pagination does exist on other collection endpoints (identities, memberships, certificates),
  which return `{ <resource>: [...], "totalCount": n }`. See
  [Pagination and Rate Limits](./pagination-and-rate-limits.md).

### Performance

- Set `viewSecretValue=false` when you only need key names
- Keep `recursive=false` unless you genuinely need subfolders — recursive reads across a deep
  tree are the main cost driver on this endpoint
- Set `expandSecretReferences=false` if you don't need `${SECRET}` resolution
- Use the `/batch` endpoints for writes; secret endpoints share a single `secretsLimit` quota
