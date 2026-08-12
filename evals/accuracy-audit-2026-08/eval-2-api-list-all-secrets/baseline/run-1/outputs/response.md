Here's the request and how paging works.

## 1. Authenticate (if you don't already have a token)

If you're using a machine identity (Universal Auth), get a short-lived access token first:

```bash
curl --request POST \
  --url "https://app.infisical.com/api/v1/auth/universal-auth/login" \
  --header "Content-Type: application/json" \
  --data '{
    "clientId": "<MACHINE_IDENTITY_CLIENT_ID>",
    "clientSecret": "<MACHINE_IDENTITY_CLIENT_SECRET>"
  }'
```

This returns `{ "accessToken": "...", "expiresIn": ..., "tokenType": "Bearer" }`. Use `accessToken` as the bearer token below. (Swap the base URL for your self-hosted instance if applicable.)

## 2. Fetch all secrets, including subfolders

```bash
curl --request GET \
  --url "https://app.infisical.com/api/v3/secrets/raw?workspaceId=<PROJECT_ID>&environment=<ENV_SLUG>&secretPath=/&recursive=true&include_imports=false" \
  --header "Authorization: Bearer <ACCESS_TOKEN>"
```

Key params:
- `workspaceId` — the project ID
- `environment` — environment slug (e.g. `dev`, `staging`, `prod`)
- `secretPath` — the folder to start at; `/` is project root
- `recursive=true` — this is what pulls in secrets from every subfolder under `secretPath`, not just the top level. Each returned secret includes its own `secretPath` so you can tell which folder it came from.
- `include_imports` — set `true` if you also want secrets pulled in via secret imports resolved

Response shape is roughly:

```json
{
  "secrets": [
    { "id": "...", "secretKey": "API_KEY", "secretValue": "...", "secretPath": "/backend/db", "version": 3, ... }
  ],
  "imports": []
}
```

## 3. Paging through large result sets

For projects with a large number of secrets, this endpoint accepts `limit` and `offset` query params so you don't pull everything in one oversized response. Pattern:

```bash
offset=0
limit=100

while :; do
  resp=$(curl -s --request GET \
    --url "https://app.infisical.com/api/v3/secrets/raw?workspaceId=<PROJECT_ID>&environment=<ENV_SLUG>&secretPath=/&recursive=true&limit=${limit}&offset=${offset}" \
    --header "Authorization: Bearer <ACCESS_TOKEN>")

  count=$(echo "$resp" | jq '.secrets | length')
  echo "$resp" | jq -c '.secrets[]'   # process/append this page

  if [ "$count" -lt "$limit" ]; then
    break
  fi
  offset=$((offset + limit))
done
```

The loop condition is: keep requesting with an increasing `offset` until a page comes back with fewer items than `limit` (or empty) — that's your signal you've reached the end, since this endpoint doesn't return a total count or next-page cursor.

A couple of things worth doing around that loop:
- **Respect rate limits.** If you get a `429`, back off and retry using the `Retry-After` header rather than hammering the endpoint.
- **Don't assume stability across pages.** If secrets are being created/deleted while you're paging, offset-based pagination can skip or duplicate items. For a one-shot export, that's usually fine; if you need a consistent snapshot, consider pinning to a point in time or re-running the export in one tight window.
- **Fallback strategy if a single recursive call is too big even paginated:** enumerate folders explicitly via `GET /api/v1/folders?workspaceId=<PROJECT_ID>&environment=<ENV_SLUG>&path=/` (also recursive-capable) and page per-folder instead of per-project — useful if you want to parallelize the export across folders.

Since I can't verify this against live docs in this session, double check exact param names against `docs.infisical.com/api-reference` before scripting this into anything production-critical — API surface details like this do shift between releases.
