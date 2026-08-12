Here are the exact values for both, pulled from the skill's generated reference.

## Okta — slug `okta`

**Method:** `api-token`

**Credentials fields (both required):**
- `instanceUrl`
- `apiToken`

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/okta' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-okta",
    "method": "api-token",
    "credentials": {
      "instanceUrl": "https://your-org.okta.com",
      "apiToken": "<okta-api-token>"
    }
  }'
```

## Datadog — slug `datadog`

Datadog accepts two method values, `token` and `api-key`, both taking the same three fields:

**Credentials fields (all required):**
- `url`
- `apiKey`
- `applicationKey`

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/datadog' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-datadog",
    "method": "api-key",
    "credentials": {
      "url": "https://api.datadoghq.com",
      "apiKey": "<datadog-api-key>",
      "applicationKey": "<datadog-application-key>"
    }
  }'
```

A note on scope: neither connection type supports `gatewayId`/`gatewayPoolId` or platform-managed credentials, so both keys live wherever you generate them (Okta admin console, Datadog Organization Settings) and Infisical just stores what you give it. Grant the minimum scopes needed on each provider's side before creating the connection.
