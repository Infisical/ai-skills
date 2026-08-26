# Pagination and Rate Limits

## Pagination

**Important:** pagination is *not* universal across the Infisical API. It exists on
collection endpoints for org- and project-level resources (identities, memberships,
certificates, secret requests, PKI subscribers, and similar). It does **not** exist on
`/api/v4/secrets`.

### `/api/v4/secrets` has no pagination

`GET /api/v4/secrets` returns every secret at the requested path in one response. It accepts
no `offset` and no `limit`. Passing them has no effect.

Accepted query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `projectId` | string | — | Project to read from |
| `environment` | string | — | Environment slug |
| `secretPath` | string | `/` | Folder path |
| `viewSecretValue` | boolean | `true` | Return actual values rather than hidden placeholders |
| `expandSecretReferences` | boolean | `true` | Resolve `${SECRET}` references |
| `recursive` | boolean | `false` | Include secrets in subfolders |
| `includeImports` | boolean | `true` | Include imported secrets |
| `includePersonalOverrides` | boolean | `false` | Include personal overrides |
| `tagSlugs` | string | — | Comma-separated tag slugs to filter by |
| `metadataFilter` | string | — | `key=k1,value=v1\|key=k2,value=v2` (max 10 pairs) |

Response shape:

```json
{
  "secrets": [
    {
      "id": "...",
      "secretKey": "DATABASE_URL",
      "secretValue": "postgres://...",
      "secretValueHidden": false,
      "secretPath": "/",
      "secretComment": "",
      "tags": [],
      "secretMetadata": []
    }
  ],
  "imports": [
    {
      "secretPath": "/shared",
      "environment": "dev",
      "secrets": [ /* ... */ ]
    }
  ]
}
```

There is no `total`, `offset`, `limit`, or `items` key. To narrow the result set, use
`secretPath`, `recursive`, `tagSlugs`, or `metadataFilter` rather than pagination.

This endpoint can also return `304 Not Modified` with an empty body when used with
conditional-request headers.

### Endpoints that do paginate

Paginated collection endpoints take `offset` and `limit` as query parameters and return the
collection alongside a `totalCount`:

```bash
curl -X GET 'https://us.infisical.com/api/v1/organization/identities?offset=0&limit=100' \
  -H "Authorization: Bearer TOKEN"
```

```json
{
  "identities": [ /* ... */ ],
  "totalCount": 150
}
```

The envelope key is named after the resource (`identities`, `memberships`, `certificates`, …),
not a generic `items`. The count field is `totalCount`, not `total`.

**Limits are per-endpoint, not global.** Do not assume 100 is the ceiling everywhere:

| Endpoint family | `limit` default | `limit` max |
|-----------------|-----------------|-------------|
| `GET /api/v1/organization/identities` | 20 | 1000 |
| `POST /api/v1/identities/search` | 50 | 100 |

Check the API reference for the endpoint you are calling. When in doubt, request a modest
limit and follow `totalCount`.

### Paginating correctly

```bash
#!/bin/bash
# Page through org identities using totalCount
API_BASE="https://us.infisical.com"
TOKEN="your_access_token"
LIMIT=100
offset=0

while :; do
  response=$(curl -s "$API_BASE/api/v1/organization/identities?offset=$offset&limit=$LIMIT" \
    -H "Authorization: Bearer $TOKEN")

  total=$(echo "$response" | jq '.totalCount')
  count=$(echo "$response" | jq '.identities | length')

  echo "$response" | jq -r '.identities[].name'

  offset=$((offset + count))
  # Stop when a short page comes back or we've covered totalCount
  if [ "$count" -eq 0 ] || [ "$offset" -ge "$total" ]; then
    break
  fi
done
```

Advance `offset` by the number of items actually returned, not by the requested limit — a
short page otherwise causes you to skip records.

### Reading all secrets (no pagination needed)

```bash
curl -s 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&recursive=true' \
  -H "Authorization: Bearer TOKEN" | jq -r '.secrets[] | "\(.secretKey)=\(.secretValue)"'
```

## Rate Limits

Rate limits apply to **both cloud and self-hosted** deployments. The difference is that
self-hosted instance administrators can change them; on cloud they are set by Infisical.

### Instance defaults

These are the built-in per-minute, per-IP defaults a self-hosted instance starts with:

| Limit | Applies to | Default (req/min) |
|-------|-----------|-------------------|
| `readLimit` | GET endpoints | 60 |
| `writeLimit` | POST, PATCH, PUT, DELETE endpoints | 200 |
| `secretsLimit` | secrets, folders, and secret-import endpoints | 60 |
| `authRateLimit` | auth/login endpoints | 60 |
| global | all requests | 600 |

Self-hosted admins can override `readLimit`, `writeLimit`, and `secretsLimit` from the
instance admin panel. Infisical Cloud applies its own limits, which vary by plan; check your
plan's documentation rather than assuming a specific number.

All limits use a 60-second window and are keyed on client IP.

### Rate limit responses

Exceeding a limit returns HTTP 429 with a message stating how long to wait:

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "statusCode": 429,
  "message": "Rate limit exceeded. Please try again in 34 seconds"
}
```

The response also carries the standard `@fastify/rate-limit` headers
(`x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-reset`, and `retry-after` on a
429). Note `x-ratelimit-reset` and `retry-after` are **seconds remaining**, not a Unix
timestamp.

### Handling rate limits

Prefer `retry-after` over computing your own backoff:

```javascript
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, options);

    if (response.status === 429) {
      // retry-after is in seconds remaining
      const retryAfter = Number(response.headers.get('retry-after'));
      const delayMs = Number.isFinite(retryAfter) && retryAfter > 0
        ? retryAfter * 1000
        : 1000 * 2 ** (attempt - 1);

      await new Promise((resolve) => setTimeout(resolve, delayMs));
      continue;
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }
  throw new Error('Max retries exceeded');
}
```

### Batch instead of looping

Secret endpoints count against `secretsLimit`, so per-secret loops burn through it fast. Use
the batch endpoints:

```bash
# Create many secrets in one request
curl -X POST 'https://us.infisical.com/api/v4/secrets/batch' \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secrets": [
      { "secretKey": "A", "secretValue": "1" },
      { "secretKey": "B", "secretValue": "2" }
    ]
  }'
```

`PATCH /api/v4/secrets/batch` and `DELETE /api/v4/secrets/batch` work the same way.

## Required Headers

```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json   # required on requests with a JSON body
```

`Content-Type` matters for POST/PATCH/PUT bodies. GET and DELETE requests without a body do
not need it.

## HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 304 | Not Modified | Conditional request on list secrets, content unchanged |
| 400 | Bad Request | Invalid parameters or request body |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate secret name or resource conflict |
| 422 | Unprocessable Entity | Request failed schema validation |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server error |

## Performance Tips

1. **Don't paginate secrets** — fetch a path once, and scope with `secretPath` / `recursive`
2. **Batch writes** — one `/batch` call instead of N single-secret calls
3. **Cache locally** — the official SDKs cache and fall back to cache on failure; do the same if hand-rolling
4. **Honor `retry-after`** — it tells you exactly how long to wait
5. **Advance offset by items returned** — not by requested limit
6. **Use `viewSecretValue=false`** when you only need key names, to avoid handling values you don't need
</content>
</invoke>
