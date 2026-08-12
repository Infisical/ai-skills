## Authenticate first

```bash
curl -X POST https://us.infisical.com/api/v1/auth/universal-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "YOUR_CLIENT_ID",
    "clientSecret": "YOUR_CLIENT_SECRET"
  }'
```

Grab `accessToken` from the response and use it as `Bearer` on everything below.

## The request

To get every secret in an environment, including subfolders, set `recursive=true` and `secretPath=/`:

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=PROJECT_ID&environment=dev&secretPath=/&recursive=true&viewSecretValue=true&offset=0&limit=100' \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

Notes on the parameters:
- `secretPath=/` plus `recursive=true` walks every subfolder under root. Without `recursive=true` you'd only get secrets sitting directly at that path.
- `viewSecretValue=true` is required if you want plaintext values back, not just metadata. Skip it if you only need names/metadata, since it's more expensive on large lists.
- `limit=100` is the max page size, use it to minimize request count.

## Paging through all of it

Response shape:

```json
{
  "secrets": [ ... ],
  "total": 245,
  "offset": 0,
  "limit": 100
}
```

Loop on `offset` until `offset + limit >= total`:

```bash
#!/bin/bash

PROJECT_ID="PROJECT_ID"
ENVIRONMENT="dev"
TOKEN="YOUR_ACCESS_TOKEN"
API_BASE="https://us.infisical.com"
LIMIT=100

offset=0
total=-1
all_secrets="[]"

while [ "$total" -eq -1 ] || [ "$offset" -lt "$total" ]; do
  response=$(curl -s -w '\n%{http_code}' \
    "$API_BASE/api/v4/secrets?projectId=$PROJECT_ID&environment=$ENVIRONMENT&secretPath=/&recursive=true&viewSecretValue=true&offset=$offset&limit=$LIMIT" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "429" ]; then
    echo "Rate limited, backing off 60s..."
    sleep 60
    continue
  elif [ "$http_code" != "200" ]; then
    echo "Error: HTTP $http_code"
    echo "$body"
    exit 1
  fi

  total=$(echo "$body" | jq '.total')
  page_count=$(echo "$body" | jq '.secrets | length')
  all_secrets=$(jq -s '.[0] + .[1].secrets' <(echo "$all_secrets") <(echo "$body"))

  echo "Fetched $((offset + page_count)) / $total"
  offset=$((offset + LIMIT))
done

echo "$all_secrets" > all_secrets.json
echo "Done. Total secrets: $(echo "$all_secrets" | jq 'length')"
```

Why this works this way:
- **Loop condition** uses `total` from the first response since it isn't known ahead of time, starting `offset=0`, incrementing by `limit` each iteration until `offset >= total`.
- **429 handling**: cloud deployments enforce rate limits (secret ops: 120/min free tier, 300/min pro tier). On a 429, back off and retry rather than failing outright. Self-hosted has no rate limit, so this branch is just insurance.
- **limit=100** minimizes the number of round trips for large secret sets (skill recommends this for anything over ~1000 secrets).
- Results are accumulated into `all_secrets.json` with `jq -s`, merging each page's `secrets` array.

One thing worth double-checking before you run this against production: `viewSecretValue=true` pulls plaintext values into that JSON file on disk, so treat `all_secrets.json` as sensitive and clean it up after use.
