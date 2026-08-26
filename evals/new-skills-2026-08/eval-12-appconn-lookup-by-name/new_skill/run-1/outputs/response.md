Yes. `GET /api/v1/app-connections/<slug>/connection-name/{connectionName}` resolves a connection by its name, and it accepts a machine identity token (it's one of the 8 CRUD routes that support identity auth — only `/usage` is JWT-only).

So your automation can skip storing UUIDs entirely: pass the connection's `slug` (e.g. `aws`, `postgres`) and its `name`, and get back the full connection object including its `id` to use as `connectionId` downstream.

Example:
```bash
curl 'https://us.infisical.com/api/v1/app-connections/aws/connection-name/prod-aws' \
  -H "Authorization: Bearer $TOKEN"
```
