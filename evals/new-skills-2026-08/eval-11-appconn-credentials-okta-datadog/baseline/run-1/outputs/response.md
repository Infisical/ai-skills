A few tool caveats first: this session doesn't have web or file/repo access, so I can't hit Infisical's docs or grep the backend source to confirm current field names live. Okta and Datadog connections may also have shipped after my training cutoff (Jan 2026), so treat the connector-specific details below as my best recollection, not a verified source.

**What's stable across all Infisical App Connections** (this pattern is consistent regardless of app):

```
POST /api/v1/app-connections/{app}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "my-connection",
  "method": "<method-value>",
  "credentials": { ... },
  "description": "optional"
}
```

`{app}` is the connector slug (`okta`, `datadog`), and the body always has `name`, `method`, `credentials`.

**My best recollection of the connector-specific values** (unverified — see below):

| App | `{app}` slug | `method` value | `credentials` fields |
|---|---|---|---|
| Okta | `okta` | `api-token` | `instanceUrl`, `apiToken` |
| Datadog | `datadog` | `api-key` | `apiKey`, `appKey`, `apiUrl` (Datadog site, e.g. `datadoghq.com`) |

Since you're at Infisical and I can't confirm these right now, the fastest ways to get ground truth before you build against them:

1. Hit `GET /api/v1/app-connections/options` on a running instance — this typically enumerates supported apps with their method/field metadata (it's what the dashboard UI uses to render the connection form).
2. Check the backend source directly: `backend/src/services/app-connection/okta/` and `backend/src/services/app-connection/datadog/`, specifically the `*-constants.ts` (method enum) and `*-schemas.ts` (Zod credentials schema) files.
3. The public API reference at `infisical.com/docs/api-reference/endpoints/app-connections/okta/create` and `.../datadog/create`.

Want me to draft the actual create-connection request bodies once you've confirmed the field names, or do you have repo/docs access you can paste in so I can write exact calls now?
