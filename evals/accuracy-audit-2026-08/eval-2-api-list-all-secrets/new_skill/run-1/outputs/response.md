Here's the exact request, plus an important correction on the paging question.

## The request

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev&secretPath=/&recursive=true' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

- `projectId` and `environment` are required.
- `secretPath=/` starts at the root.
- `recursive=true` is what pulls in subfolders. Without it, you only get secrets at exactly `secretPath`.

If you only need key names (not values), add `viewSecretValue=false` to skip returning plaintext values.

Get a token first via Universal Auth:

```bash
curl -X POST 'https://us.infisical.com/api/v1/auth/universal-auth/login' \
  -H "Content-Type: application/json" \
  -d '{"clientId": "YOUR_CLIENT_ID", "clientSecret": "YOUR_CLIENT_SECRET"}'
```

Use the returned `accessToken` as the Bearer token above.

## On paging: there isn't any here

This is the important part: `/api/v4/secrets` is **not paginated**. It returns every secret at the requested path (and subfolders, with `recursive=true`) in a single response. It ignores `offset` and `limit` entirely if you pass them, so there's no page loop to write for this call.

The response shape is:

```json
{
  "secrets": [ { "secretKey": "...", "secretValue": "...", ... } ],
  "imports": [ ... ]
}
```

No `total`, `offset`, `limit`, or `items` field, since there's nothing to paginate.

If a project is large enough that a single recursive pull feels too big, the way to control result size is by narrowing scope, not paging:
- Split the pull by `secretPath` (walk subfolders individually instead of one big `recursive=true` call)
- Filter with `tagSlugs` or `metadataFilter`
- Set `viewSecretValue=false` if you don't need values, and `expandSecretReferences=false` if you don't need `${SECRET}` expansion resolved

Pagination (`offset`/`limit` with a `totalCount` field) exists on other collection endpoints like `/api/v1/organization/identities` or memberships/certificates, but not on secrets. If you were expecting to loop with offset/limit against this endpoint, that logic isn't needed here.

One more thing worth handling defensively: this endpoint can return `304 Not Modified` with an empty body on a conditional request, so if you're scripting this, don't assume every call returns a body.
