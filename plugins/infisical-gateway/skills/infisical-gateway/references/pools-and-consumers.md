# Gateway Pools and What Can Use a Gateway

## Gateway Pools

A pool is a **named collection of gateways that all have connectivity to the same private network**.
Enterprise feature.

### How it works

1. Create a pool and add multiple gateways that share network access to the same resources
2. When configuring a consumer, select the **pool** instead of an individual gateway
3. At request time the platform picks a **random healthy gateway** from the pool
4. If a gateway goes down, subsequent requests route through the remaining healthy members

A gateway counts as healthy if it has sent a successful heartbeat within its TTL window (heartbeats
every 3 minutes).

### The requirement people get wrong

**Every gateway in a pool must be able to reach the same resources.** Routing is random, so a pool
containing one gateway in the prod VPC and one in staging will work roughly half the time and fail the
rest — which is worse than a single gateway, because the failure is intermittent and looks like a
flaky network.

A pool is for redundancy across gateways in the *same* network. It is not a way to cover multiple
networks with one configuration.

### Creating one

**Organization Settings → Networking → Gateways → Gateway Pools tab → Create Pool**, then add
gateways to the pool from its detail view.

### When to use a pool

Use one for **anything production**. A single gateway is a single point of failure for every feature
routed through it — dynamic secrets stop issuing, rotations fail, PAM sessions cannot open.

Two gateways on separate hosts (ideally separate availability zones) in a pool removes that.

Note relay failover and gateway pooling are independent: automatic relay selection protects against a
relay going away, but does nothing if the gateway host itself dies.

## Attaching a gateway

Consumers take either `gatewayId` (a specific gateway) or `gatewayPoolId` (a pool).

**They are mutually exclusive.** Setting both fails with
`Cannot specify both a gateway and a gateway pool`.

Prefer `gatewayPoolId` in production even if the pool currently has one member — then adding a second
gateway later needs no reconfiguration of every consumer.

## App Connections that accept a gateway

Only these **16** connection types support `gatewayId` / `gatewayPoolId`:

`adcs`, `azure-key-vault`, `f5-big-ip`, `github`, `hashicorp-vault`, `kemp-loadmaster`, `ldap`,
`mssql`, `mysql`, `netscaler`, `nutanix-prism-central`, `postgres`, `smb`, `ssh`, `venafi-tpp`,
`winrm`

Passing a gateway to any other connection type is a **validation error**:
`Not supported for <Name> Connections`. It is not silently ignored.

Consequence worth stating: if a user needs to reach a private service whose connection type is **not**
on this list, a gateway will not help. They need actual network reachability — a public endpoint, a
VPN, or peering. Say so rather than suggesting a gateway that cannot be attached.

See `infisical-app-connections` for the full connection catalog.

## Dynamic secret providers that accept a gateway

| Provider | Notes |
|----------|-------|
| `sql-database` | Covers postgres, mysql2, oracledb, mssql, sap-ase, vertica |
| `azure-sql-database` | |
| `clickhouse` | |
| `vertica` | |
| `milvus` | |
| `kubernetes` | Also used by Kubernetes Auth's Gateway review mode |

This is the most common gateway use case overall: a VPC-only RDS instance that needs to issue
short-lived credentials. See `infisical-dynamic-secrets`.

## Other consumers

| Consumer | Why it needs a gateway |
|----------|-----------------------|
| **Kubernetes Auth** (review mode `Gateway`) | Validating service account tokens against a cluster API server that is not publicly reachable. See `infisical-setup` |
| **PAM** | Sessions are proxied through a gateway, and in agentic access the gateway is what injects the real credential. See `infisical-pam` |
| **PKI external CAs** | ADCS, Azure ADCS, and Venafi TPP are typically on internal networks. See `infisical-pki` |
| **PKI certificate syncs** | NetScaler, F5 BIG-IP, Kemp LoadMaster, Nutanix, Linux/Windows servers are internal targets |
| **HSM connectors** | The gateway loads the vendor's PKCS#11 driver and bridges to the HSM — Infisical never talks to it directly. See `infisical-pki` |
| **Secret rotations** | Rotations against internal databases, LDAP, or OS accounts, via their App Connection |

The HSM case is architecturally notable: the gateway is not just a network hop there, it is the
component that actually performs the PKCS#11 operations. An HSM connector without a working gateway
cannot function at all.

## Planning a gateway topology

Work it out from the resources, not from the features:

1. **List the private resources** Infisical must reach
2. **Group them by network** — one gateway (or pool) per isolated network with direct connectivity to that group
3. **For each group, deploy two gateways** on separate hosts and put them in a pool
4. **Decide the relay strategy** per region — managed unless latency or policy says otherwise
5. **Confirm each consuming connection type supports a gateway** before promising it will work
6. **Get the egress rules approved early** — TCP 2222 to the relay, TCP 443 to Infisical, and settle the auto-select-relay allowlist question up front

Worked example — prod and staging VPCs plus an on-prem datacenter:

| Network | Gateways | Pool | Reaches |
|---------|----------|------|---------|
| prod VPC | 2, separate AZs | `prod-vpc` | RDS, internal API |
| staging VPC | 1 (non-critical) | — | staging RDS |
| on-prem DC | 2, separate hosts | `onprem` | ADCS, domain controller, HSM |

Three networks, three gateway groups. Do not attempt to serve all three from one gateway, and do not
put gateways from different networks in the same pool.
