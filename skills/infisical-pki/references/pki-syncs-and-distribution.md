# PKI Syncs, Alerting, and Discovery

## PKI Syncs

A PKI Sync pushes issued certificates from Infisical to a system that terminates TLS, so you never
hand-install a certificate again. Configured on an Application.

This is the certificate analogue of a Secret Sync, and it works the same way: it needs an App
Connection, it has a destination config, and it runs automatically.

### All 12 PKI Syncs

| Destination | `destination` value | App Connection |
|-------------|--------------------|----------------|
| Azure Key Vault | `azure-key-vault` | `azure-key-vault` |
| AWS Certificate Manager | `aws-certificate-manager` | `aws` |
| AWS Secrets Manager | `aws-secrets-manager` | `aws` |
| AWS Elastic Load Balancer | `aws-elastic-load-balancer` | `aws` |
| Cloudflare Custom SSL Certificate | `cloudflare-custom-certificate` | `cloudflare` |
| NetScaler | `netscaler` | `netscaler` |
| F5 BIG-IP | `f5-big-ip` | `f5-big-ip` |
| Kemp LoadMaster | `kemp-loadmaster` | `kemp-loadmaster` |
| Nutanix Prism Central | `nutanix-prism-central` | `nutanix-prism-central` |
| Chef | `chef` | `chef` |
| Linux Server | `linux-server` | **`ssh`** |
| Windows Server | `windows-server` | **`winrm`** |

Note the last two: "Linux Server" and "Windows Server" are not their own connection types. They
use `ssh` and `winrm` connections respectively. That catches people out when they go looking for a
"linux-server" App Connection that does not exist.

### Sync status and actions

`PkiSyncStatus`: `pending`, `running`, `succeeded`, `failed`

`PkiSyncAction`:

| Action | Meaning |
|--------|---------|
| `sync-certificates` | Push certificates to the destination |
| `import-certificates` | Pull existing certificates from the destination into Infisical |
| `remove-certificates` | Remove certificates from the destination |

`import-certificates` is the useful one for migration — point a sync at a load balancer that
already holds certificates and bring them under management rather than reissuing everything.

### Choosing a destination

| The certificate terminates at... | Sync |
|---------------------------------|------|
| An AWS ALB/NLB | `aws-elastic-load-balancer`, or `aws-certificate-manager` if you attach via ACM |
| CloudFront, API Gateway, anything ACM-backed | `aws-certificate-manager` |
| An application reading the cert as a secret | `aws-secrets-manager` |
| Azure services | `azure-key-vault` |
| Cloudflare edge | `cloudflare-custom-certificate` |
| An on-prem load balancer | `netscaler`, `f5-big-ip`, `kemp-loadmaster` |
| A plain Linux host's filesystem | `linux-server` (over SSH) |
| A Windows host's certificate store | `windows-server` (over WinRM) |
| Nutanix infrastructure | `nutanix-prism-central` |
| Config-managed fleet | `chef` |

The on-premises destinations (NetScaler, F5, Kemp, Nutanix, Linux, Windows) almost always need a
**Gateway**, since they are internal. Their App Connection types all support `gatewayId`. See
`infisical-gateway`.

### AWS Certificate Manager caveat

ACM is region-scoped, and some AWS services require the certificate in a specific region —
CloudFront requires `us-east-1` regardless of where the rest of your infrastructure lives. If a
user's CloudFront distribution cannot see the synced certificate, wrong region is the first thing
to check.

## Alerting

Alerting is configured per Application and is the control that prevents silent expiry. Three
channels:

| Channel | Doc |
|---------|-----|
| Webhook | `webhook-alerts` |
| Slack | `slack-alerts` |
| PagerDuty | `pagerduty-alerts` |

Alertable events include expiration, issuance, renewal, and revocation.

Guidance worth giving unprompted:

- **Alert on expiration well ahead of time.** A warning the day before is useless if renewal needs a change request. 30 and 7 days out is a reasonable pair.
- **Alert on issuance too**, not just expiry. An unexpected issuance is a security signal — someone got a certificate for your domain.
- **Route expiry to a channel someone reads.** PagerDuty for anything whose expiry would be an incident; Slack for informational.

An Application with automated renewal but no alerting is still fragile: renewal can fail (CA
unreachable, approval pending, DNS challenge broken) and without an alert the first symptom is an
outage.

## Certificate discovery

Discovery scans your network for certificates Infisical did not issue.

Two modes documented: an overview of the feature and **network** scanning.

What it is for:

- **Migration.** Find every certificate in the estate before deciding what to bring under management.
- **Finding the forgotten ones.** The certificate that takes production down is usually on a host nobody remembers, issued by someone who has left.
- **Ongoing inventory.** Detect certificates issued outside your process.

Workflow: discover, review what turns up, then either import via a PKI Sync's
`import-certificates` action or reissue through an Application so the certificate is managed going
forward.

Discovery is read-only reconnaissance. It does not take ownership of anything by itself.

## Bringing an existing PKI onto Infisical

A sensible order when a user is migrating:

1. **Discover** what exists
2. **Stand up the CA story** — either import/reuse an existing CA as an external CA, or create an internal hierarchy and plan a trust rollout
3. **Model the guardrails** as Policies and Profiles
4. **Create Applications** per service, matching how teams are organized
5. **Configure enrollment** matching what each client population supports
6. **Add PKI Syncs** for destinations that currently receive certificates by hand
7. **Turn on renewal and alerting** before decommissioning the old process

The step people skip is 7, and it is the one that matters. Do not let a migration finish with
renewal still living in someone's calendar.
