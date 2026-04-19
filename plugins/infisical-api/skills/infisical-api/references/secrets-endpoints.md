# Secrets Endpoints

All secret operations use `/api/v4/secrets`. Previous API versions (v1, v2, v3) are deprecated.

## List Secrets

### Endpoint

```
GET /api/v4/secrets
```

### Query Parameters

| Parameter | Type | Required | Default | Max | Description |
|-----------|------|----------|---------|-----|-------------|
| projectId | string | Yes | - | - | ID of the project |
| environment | string | Yes | - | - | Environment slug (e.g., "dev", "prod") |
| secretPath | string | No | "/" | - | Secret folder path (e.g., "/database", "/") |
| offset | integer | No | 0 | - | Number of items to skip for pagination |
| limit | integer | No | 20 | 100 | Number of items to return per page |
| viewSecretValue | boolean | No | false | - | Include plaintext secret values in response |
| expandSecretReferences | boolean | No | false | - | Expand secret references (e.g., `${OTHER_SECRET}`) |
| recursive | boolean | No | false | - | Include secrets from all subdirectories |
| includeImports | boolean | No | false | - | Include secrets from imported secret environments |
| tagSlugs | string | No | - | - | Comma-separated tag slugs to filter by |
| metadataFilter | string | No | - | - | JSON filter for metadata-based search |

### Response

```json
{
  "secrets": [
    {
      "id": "secret-id-uuid",
      "version": 1,
      "workspace": "workspace-id",
      "project": "project-id",
      "environment": "dev",
      "secretPath": "/",
      "secretName": "DATABASE_URL",
      "secretValue": "postgres://user:pass@localhost/db",
      "secretComment": "Production database connection",
      "type": "shared",
      "tags": [
        {
          "id": "tag-id",
          "slug": "database",
          "name": "Database",
          "color": "#3b82f6"
        }
      ],
      "createdAt": "2026-04-16T10:30:00.000Z",
      "updatedAt": "2026-04-16T10:30:00.000Z",
      "createdBy": "user-id"
    }
  ],
  "total": 42,
  "offset": 0,
  "limit": 20
}
```

### Example

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&offset=0&limit=20&viewSecretValue=true' \
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

### Response

```json
{
  "secret": {
    "id": "secret-id-uuid",
    "version": 1,
    "workspace": "workspace-id",
    "project": "project-id",
    "environment": "dev",
    "secretPath": "/",
    "secretName": "API_KEY",
    "secretValue": "sk_live_abc123def456ghi789",
    "secretComment": "Third-party API key",
    "type": "shared",
    "tags": [],
    "createdAt": "2026-04-16T10:30:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z",
    "createdBy": "user-id"
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
| secretComment | string | No | Comment/description for the secret |

### Response

```json
{
  "secret": {
    "id": "secret-id-uuid",
    "version": 1,
    "workspace": "workspace-id",
    "project": "project-id",
    "environment": "dev",
    "secretPath": "/",
    "secretName": "NEW_SECRET",
    "secretValue": "super-secret-value",
    "secretComment": "My new secret",
    "type": "shared",
    "tags": [],
    "createdAt": "2026-04-16T10:30:00.000Z",
    "updatedAt": "2026-04-16T10:30:00.000Z",
    "createdBy": "user-id"
  }
}
```

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

### Response

Same as Create Secret response.

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
    "secretName": "DELETED_SECRET"
  }
}
```

### Example

```bash
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/OLD_SECRET?projectId=abc123&environment=dev&secretPath=/' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Batch Delete Secrets

### Endpoint

```
DELETE /api/v4/secrets/batch
```

### Request Body

```json
{
  "projectId": "string",
  "environment": "string",
  "secretPath": "string",
  "secretIds": ["uuid1", "uuid2", "uuid3"]
}
```

### Response

```json
{
  "deletedSecrets": [
    {
      "id": "uuid1",
      "secretName": "SECRET_1"
    },
    {
      "id": "uuid2",
      "secretName": "SECRET_2"
    }
  ]
}
```

### Example

```bash
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/batch' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secretIds": ["id1-uuid", "id2-uuid"]
  }'
```

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

- Always specify `offset` and `limit` for predictable results
- Default limit is 20; maximum is 100
- Use `total` to determine remaining items: `hasMore = (offset + limit) < total`

### Performance

- For listing many secrets (>1000), use pagination with `limit=100`
- Avoid `viewSecretValue=true` on large lists unless values are needed
- Use `recursive=false` by default for better performance
