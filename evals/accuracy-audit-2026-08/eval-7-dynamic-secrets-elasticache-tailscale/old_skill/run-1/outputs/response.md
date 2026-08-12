Based on this skill's provider list, the answer differs for each:

**AWS ElastiCache — supported, via the Redis provider**
ElastiCache isn't a distinct provider; it's explicitly called out as an example of managed Redis under the **Redis** dynamic secret type. Configure it like standard Redis:

| Field | Notes |
|---|---|
| Host / Port | ElastiCache endpoint, port default `6379` |
| User | Admin user (`default` or an admin ACL user) with permission to create ACL users |
| Password | If your ElastiCache instance requires auth |
| CA (SSL) | The skill flags that managed Redis services like ElastiCache "often require SSL" — use this field |

Requires Redis 6+ ACL support (ElastiCache supports this on newer engine versions). Leases return `DB_USERNAME` / `DB_PASSWORD`. You can customize the ACL statement for least privilege, e.g. `ACL SETUSER {{username}} on >{{password}} ~app:* +get +mget +scan +keys`.

**Tailscale — not supported**
Tailscale doesn't appear anywhere in this skill's list of 27 providers (SQL databases, NoSQL/cache, cloud IAM, or the SSH/Kubernetes infrastructure providers). I don't have a reference for it, so I can't give you configuration steps or restrictions, and I'd rather tell you that than guess. If you have a specific reason to think Infisical added Tailscale support, worth checking Infisical's current docs directly since this skill may not reflect the newest providers.
