# Pagination and Rate Limits

## Pagination

Infisical uses offset-based pagination for list endpoints. All responses include pagination metadata.

### Pagination Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| offset | integer | 0 | - | Number of items to skip from the beginning |
| limit | integer | 20 | 100 | Maximum number of items to return in this request |

### Pagination Response

```json
{
  "items": [...],
  "total": 150,
  "offset": 0,
  "limit": 20
}
```

- **total**: Total count of all available items (ignoring pagination)
- **offset**: Requested offset
- **limit**: Requested limit (may be less if fewer items available)
- **items**: Array of results for this page

### Example: Paginating Through All Results

```bash
#!/bin/bash

# Retrieve all secrets in batches of 20
offset=0
limit=20
total=-1

while [ $offset -lt $total ] || [ $total -eq -1 ]; do
  response=$(curl -s "https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&offset=$offset&limit=$limit" \
    -H "Authorization: Bearer TOKEN")
  
  # Extract items and total from response
  total=$(echo $response | jq '.total')
  items=$(echo $response | jq '.secrets[]')
  
  # Process items
  echo "Processing items $offset to $((offset + limit))..."
  
  offset=$((offset + limit))
done
```

### Pagination Best Practices

1. **Start with offset=0**: Always begin pagination at offset 0
2. **Use maximum limit**: Set `limit=100` for faster retrieval (unless you need fewer items)
3. **Check total**: Use the `total` value to determine if more pages exist: `hasMore = (offset + limit) < total`
4. **Handle edge cases**: Always check if `limit` in response is less than requested (indicates fewer items available)
5. **Respect rate limits**: Add delays between requests if hitting rate limits

## Rate Limits (Cloud Only)

Infisical Cloud deployments have rate limits. Self-hosted deployments have no rate limits.

### Rate Limit Types

#### Read Operations (GET, LIST)

- **Free Tier**: 200 reads per minute
- **Pro Tier**: 350 reads per minute
- **Enterprise**: Custom limits

#### Write Operations (CREATE, UPDATE, DELETE)

- **Free Tier**: 90 writes per minute
- **Pro Tier**: 200 writes per minute
- **Enterprise**: Custom limits

#### Secret Operations (All /api/v4/secrets/* endpoints)

- **Free Tier**: 120 secret ops per minute
- **Pro Tier**: 300 secret ops per minute
- **Enterprise**: Custom limits

### Rate Limit Response Headers

When you hit a rate limit, the API returns HTTP 429 (Too Many Requests):

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1713350400
Content-Type: application/json

{
  "statusCode": 429,
  "message": "Too many requests, please try again later."
}
```

- **X-RateLimit-Limit**: Maximum requests allowed in the window
- **X-RateLimit-Remaining**: Requests remaining in the current window
- **X-RateLimit-Reset**: Unix timestamp when the limit resets

### Handling Rate Limits

#### Implement Exponential Backoff

```javascript
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      const resetTime = parseInt(response.headers.get('X-RateLimit-Reset')) * 1000;
      const delayMs = Math.max(resetTime - Date.now(), 1000 * Math.pow(2, attempt - 1));
      
      console.log(`Rate limited. Waiting ${delayMs}ms before retry...`);
      await new Promise(resolve => setTimeout(resolve, delayMs));
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

#### Monitor Rate Limit Usage

```bash
curl -s 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&limit=1' \
  -H "Authorization: Bearer TOKEN" \
  -w "\nRate Limit Remaining: %{http_header{X-RateLimit-Remaining}}\n"
```

#### Batch Operations

Group multiple operations to reduce request count:

```bash
# Instead of 100 DELETE requests, use one batch delete
curl -X DELETE 'https://us.infisical.com/api/v4/secrets/batch' \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "abc123",
    "environment": "dev",
    "secretPath": "/",
    "secretIds": ["id1", "id2", "id3", ...]
  }'
```

#### Request Queuing

Implement a request queue to spread requests over time:

```python
import asyncio
import aiohttp
from collections import deque

class RateLimitedClient:
    def __init__(self, requests_per_minute=200):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60 / requests_per_minute
        self.last_request_time = 0
        self.queue = deque()
    
    async def request(self, session, method, url, **kwargs):
        # Wait if necessary to maintain rate limit
        elapsed = asyncio.get_event_loop().time() - self.last_request_time
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        
        async with session.request(method, url, **kwargs) as response:
            self.last_request_time = asyncio.get_event_loop().time()
            return await response.json()
```

## Required Headers

All API requests must include:

```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Example: Complete Request with Headers

```bash
curl -X GET 'https://us.infisical.com/api/v4/secrets?projectId=abc123&environment=dev&offset=0&limit=20' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid parameters or request body |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate secret name or resource conflict |
| 429 | Too Many Requests | Rate limit exceeded (cloud only) |
| 500 | Internal Error | Server error |

## Performance Tips

1. **Use pagination**: Limit each request to 100 items maximum
2. **Cache responses**: Store secret values locally to reduce API calls
3. **Use appropriate timeouts**: Set 30-second timeouts for API calls
4. **Batch operations**: Combine multiple operations into single requests where possible
5. **Monitor headers**: Check X-RateLimit-Remaining to anticipate throttling
6. **Implement exponential backoff**: Automatically retry failed requests with increasing delays
7. **Use webhooks**: Subscribe to changes instead of polling for updates (if available)

## Example: Comprehensive Pagination with Error Handling

```bash
#!/bin/bash

PROJECT_ID="abc123"
ENVIRONMENT="dev"
API_BASE="https://us.infisical.com"
TOKEN="your_access_token"
BATCH_SIZE=100

offset=0
total_processed=0

while true; do
  # Make request with error handling
  response=$(curl -s -w "\n%{http_code}" \
    "$API_BASE/api/v4/secrets?projectId=$PROJECT_ID&environment=$ENVIRONMENT&offset=$offset&limit=$BATCH_SIZE" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")
  
  # Extract body and status code
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | head -n-1)
  
  # Check for errors
  if [ "$http_code" = "429" ]; then
    reset_time=$(curl -s -I "$API_BASE/api/v4/secrets?projectId=$PROJECT_ID&environment=$ENVIRONMENT" \
      -H "Authorization: Bearer $TOKEN" | grep X-RateLimit-Reset | awk '{print $2}')
    echo "Rate limited. Waiting until $reset_time..."
    sleep 60
    continue
  elif [ "$http_code" != "200" ]; then
    echo "Error: HTTP $http_code"
    echo "$body" | jq .
    exit 1
  fi
  
  # Process response
  total=$(echo "$body" | jq '.total')
  count=$(echo "$body" | jq '.secrets | length')
  
  echo "Processing items $offset-$((offset + count)) of $total..."
  
  # Do something with the secrets
  echo "$body" | jq '.secrets[] | .secretName'
  
  total_processed=$((total_processed + count))
  
  # Check if we've retrieved all items
  if [ $total_processed -ge $total ]; then
    break
  fi
  
  offset=$((offset + BATCH_SIZE))
done

echo "Processed $total_processed items total"
```
