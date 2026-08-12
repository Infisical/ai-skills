Here are the exact rules, straight from the Gateway/Relay architecture:

## Gateway host (in your VPC, next to the RDS instance)

Allow **outbound only** — no inbound rules at all:

| Destination | Port | Protocol | Direction |
|---|---|---|---|
| Relay server (managed or self-hosted) | **2222** | TCP (SSH) | egress |
| Infisical instance host (`app.infisical.com` / `eu.infisical.com` / your self-hosted domain) | **443** | TCP (HTTPS) | egress |
| The RDS instance | **5432** (or whatever port Postgres/MySQL is listening on) | TCP | egress, local |

The gateway dials out to the relay and holds that connection open. Infisical routes requests back down that same outbound tunnel, so nothing needs to reach the gateway host from outside.

## If you're using the default managed relay ("Auto Select Relay")

There's no single IP to allowlist, since the gateway can fail over between managed relay endpoints. Flag this to your security team now, since it's the step that stalls deployments in locked-down networks. Two options:

- Allowlist the full set of managed relay endpoints, or
- Pin to one specific relay instead of auto-select, trading failover for a single stable IP

## Only if you self-host the relay yourself

The relay host (not the gateway) needs inbound rules:

| Source | Port | Direction |
|---|---|---|
| Your gateways | **2222** | inbound |
| Infisical instance host | **8443** | inbound |
| Infisical instance host | **443** | outbound |

## One more thing worth flagging to security

RDS access through a gateway requires a supported App Connection type — `postgres` or `mysql` are both on the list of 16 connection types that accept a gateway, so you're fine there. Also confirm the gateway sits in the same VPC as the RDS instance with direct connectivity — a gateway elsewhere with no peering can be perfectly "healthy" and still never reach the database.
