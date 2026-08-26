Yes, both are supported. I don't have live doc access in this session, so treat exact field names below as approximate and worth a quick cross-check against the current docs, but the architecture and restrictions are accurate to how each integration works.

## AWS ElastiCache

Infisical mints short-lived ElastiCache users authenticated via IAM (not static passwords), then deletes them when the lease expires.

**What you need to configure:**
- An AWS connection in Infisical (access key/secret or an assumable IAM role) with permissions to manage ElastiCache users — create, modify, delete, describe.
- Your target ElastiCache replication group/cluster must already have IAM authentication enabled.
- An existing ElastiCache **User Group** for the dynamic users to attach to — this is what actually defines the access string/permissions each temporary user gets, since ElastiCache requires every user to belong to a group.
- In the dynamic secret config: pick the AWS connection, region, and replication group, then point at that user group.
- Set the lease TTL / max TTL.
- Consumers authenticate to the Redis endpoint using IAM auth token generation with the username Infisical generated.

## Tailscale

Infisical generates ephemeral Tailscale auth keys on demand rather than credentials in the DB-rotation sense.

**What you need to configure:**
- A Tailscale OAuth client (created in the Tailscale admin console) scoped with the `auth_keys` write permission.
- The OAuth client ID/secret added to the dynamic secret config in Infisical, plus your tailnet name.
- ACL tags configured in your tailnet policy file — required because Tailscale ties OAuth client permissions to tags, so any key minted must carry at least one tag the client is authorized for.
- Key behavior settings: ephemeral/reusable/pre-authorized flags, and the lease TTL.

**Restriction to know about:** revocation is asymmetric. If the Infisical lease expires before the key is ever redeemed, the unused key is invalidated — fine. But once a device actually uses the key to join the tailnet, deleting/expiring that key does **not** remove the device from the network. The node stays joined until someone manually removes it in the Tailscale admin console (or it disconnects, if you set the key as ephemeral). So the lease TTL governs how long an *unused* key is valid, not how long a device stays connected — plan node lifecycle (ephemeral keys, separate offboarding) accordingly rather than assuming lease expiry = access revoked.

If you want, I can look at how you're planning to wire either of these into an app and sanity-check the config before you build it.
