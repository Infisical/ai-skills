# Gateway Deployment and Networking

## Ports and connections

| Connection | Source | Destination | Port | Protocol | Direction |
|-----------|--------|-------------|------|----------|-----------|
| Relay tunnel | Gateway | Relay server | **2222** | TCP (SSH) | **egress** |
| Infisical API | Gateway | Infisical instance host | **443** | TCP (HTTPS) | **egress** |
| Platform ↔ relay | Infisical platform | Relay server | **8443** | TCP + TLS | — |
| Resource access | Gateway | Private resource | the resource's own port (e.g. 5432) | TCP or HTTP | local |

Resource access is raw TCP for most resources such as databases, and HTTP for resources like
Kubernetes.

## Egress allowlist — the gateway host

Allow **outbound only**:

- **TCP 2222** to the relay server (managed relay address, or your self-hosted relay)
- **TCP 443** to the Infisical instance host — `app.infisical.com` (US), `eu.infisical.com` (EU), or your self-hosted domain

**No inbound rules are required.** If someone is asking which inbound port to open, the answer is
none. The platform reaches the gateway back down the gateway's own outbound SSH tunnel.

### The Auto Select Relay wrinkle

With the default **Auto Select Relay** option there is **no single relay address to allowlist**,
because the gateway may fail over between managed relays.

That matters for restrictive environments where the security team wants one IP in the rule. Two
options:

1. Allowlist the full set of managed relay endpoints
2. **Pin to a single relay** instead of auto-select, trading failover for a stable allowlist entry

Raise this early. A gateway deployment inside a tightly controlled network will stall on exactly this
question, and discovering it after the change request is filed is expensive.

## Self-hosted relay

If you run your own relay, that host needs:

- **Inbound TCP 2222** from your gateways (the SSH reverse tunnels)
- **Inbound TCP 8443** from the Infisical instance host (platform ↔ relay)
- **Outbound TCP 443** to the Infisical instance host (relay API + certificates)

Note the relay **does** take inbound connections — it is the gateway that never does.

### Managed vs self-deployed relays

| Option | Trade-off |
|--------|-----------|
| **Infisical-managed** | Pre-deployed relays in select regions, shared across Cloud organizations. Each organization's traffic is isolated and encrypted. No operational burden |
| **Self-deployed** | Your own dedicated relays, placed geographically close to your infrastructure for lower latency. You operate them |

Default to **managed**. Reach for self-deployed when latency genuinely matters — a relay on another
continent adds a round trip to every operation — or when policy requires that no third-party
infrastructure sit in the path.

Traffic is double-encrypted and the relay cannot decrypt it, so a managed relay is not seeing your
data.

## Deploying a gateway

Two enrollment methods: a one-time **token**, or **AWS** authentication.

### As a systemd service (recommended for hosts)

```bash
sudo infisical gateway systemd install <gateway-name> \
  --enroll-method=token \
  --token=<enrollment-token> \
  --domain=<your-infisical-domain>

sudo systemctl start <gateway-name>
```

### In the foreground (for testing)

```bash
infisical gateway start <gateway-name> \
  --enroll-method=token \
  --token=<enrollment-token> \
  --domain=<your-infisical-domain>
```

### AWS enrollment

Instead of a token, authenticate with the host's AWS identity:

```bash
sudo infisical gateway systemd install <gateway-name> \
  --enroll-method=aws \
  --gateway-id=<gateway-id> \
  --domain=<your-infisical-domain>

sudo systemctl start <gateway-name>
```

Note the flag difference: token enrollment passes `--token`, AWS enrollment passes `--gateway-id`.

Prefer AWS enrollment on EC2 — there is no enrollment token to distribute or leak, and re-enrollment
after a host replacement needs no secret.

### Kubernetes

A Helm-based deployment path exists for running the gateway in-cluster. Suits a gateway whose target
resources are reachable from inside the cluster.

### Relays

Self-deployed relays use the same shape:

```bash
infisical relay start ...
infisical relay systemd ...
```

There is also a **Terraform** path for relay deployment.

## Health checks

| Component | Heartbeat interval | Considered unhealthy when |
|-----------|-------------------|---------------------------|
| **Gateway** | Every **3 minutes** | No successful heartbeat before the TTL in the last one expires |
| **Relay** | **Hourly** | No heartbeat received within one hour |

Each gateway heartbeat carries a TTL saying how long the gateway should be considered healthy.

Infisical **notifies all organization admins** of unhealthy gateway or relay status by email and
in-app notification.

Practical consequence: a gateway that dies is detected within minutes, but a **relay** may take up to
an hour to be flagged. Do not conclude a relay is fine because Infisical has not complained yet.

## High availability

Two independent mechanisms:

1. **Relay failover** — a gateway using automatic relay selection switches to a different healthy relay if the current one becomes unreachable. Built in, no configuration.
2. **Gateway Pools** — group multiple gateways so the platform routes through a healthy member if one goes down. See `references/pools-and-consumers.md`.

Note relay failover is free but gateway-level redundancy is not: a single gateway going down breaks
every feature routed through it, regardless of relay health. For production, use a pool.

## Troubleshooting

Work through in this order:

1. **Egress.** Can the host reach the relay on TCP 2222 and the Infisical host on 443? This is the cause most of the time.
2. **Auto-select relay vs a pinned allowlist.** If only one relay IP is allowlisted and auto-select is on, connectivity works until it fails over.
3. **Is the gateway healthy?** Check status in Infisical; remember the 3-minute heartbeat.
4. **Is the gateway in the right network?** It needs direct connectivity to the target. A gateway in a different VPC with no peering cannot reach the database no matter how healthy it is.
5. **Can the gateway reach the resource locally?** From the gateway host, test the resource's own port directly.
6. **Does the consuming connection support a gateway?** Only 16 App Connection types do — see `references/pools-and-consumers.md`.
7. **Both `gatewayId` and `gatewayPoolId` set?** That is a validation error; pick one.

The distinction worth holding onto: a gateway can be perfectly healthy and still fail to reach a
resource, because health means "connected to Infisical," not "can reach your database."
