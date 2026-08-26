Short answer: yes to both, with one caveat worth checking.

**Resolving the ID by name**

Infisical's App Connections API is organized by connection type, e.g.:

- `GET /api/v1/app-connections/{app}` — lists all connections of that type (e.g. `aws`, `github`, `postgres`), each item including `id` and `name`
- `GET /api/v1/app-connections/{app}/{connectionId}` — get a single connection by ID

I'm not confident there's a dedicated "get by name" endpoint the way secrets support path/name lookups. The reliable pattern is: list connections for the app type, filter client-side for the exact `name` match, and pull that item's `id`. Names are enforced unique per org for a given connection type, so an exact match should resolve to exactly one connection.

**Machine identity token**

Yes. A machine identity authenticates (Universal Auth, AWS/GCP/Azure auth, OIDC, etc.) and gets a short-lived access token, which is then sent as a normal `Authorization: Bearer <token>` header. Infisical's permission checks are identity-agnostic, they don't care whether the Bearer token belongs to a user or a machine identity, only what role/permissions that identity has. So the same list/get App Connections calls work from automation.

The one thing to verify on your end: App Connections have historically required a fairly privileged role (Org Admin, in older versions) rather than a fine-grained "read app-connections" permission. If your machine identity has a lower-privileged custom role, confirm it can actually list connections, not just that the token authenticates.

I don't have live web access in this session, so I'd sanity-check the exact endpoint paths against your Infisical instance's `/api/v1/app-connections` docs before wiring this into automation, since this API surface has been evolving.
