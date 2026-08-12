# App Connections: Databases, Directories, and Infrastructure

These connection types most often sit behind a firewall, so this is also where Gateway routing and
platform-managed credentials matter.

## SQL databases — `postgres`, `mysql`, `mssql`

Method: `username-and-password` (note the `and`).

All three share one credential shape:

```json
{
  "name": "prod-postgres",
  "method": "username-and-password",
  "credentials": {
    "host": "db.internal.example.com",
    "port": 5432,
    "database": "app_production",
    "username": "infisical_admin",
    "password": "...",
    "sslEnabled": true,
    "sslRejectUnauthorized": true,
    "sslCertificate": "-----BEGIN CERTIFICATE-----\n..."
  },
  "gatewayId": "<gateway-uuid>"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `host` | Yes | |
| `port` | Yes | Coerced from string, so `"5432"` is accepted |
| `database` | Yes | |
| `username` | Yes | |
| `password` | Yes | |
| `sslEnabled` | Yes | Not optional — state it explicitly |
| `sslRejectUnauthorized` | Yes | Set `false` only for self-signed certs you cannot supply |
| `sslCertificate` | No | CA certificate for verification. Empty string is treated as unset |

Prefer supplying `sslCertificate` over setting `sslRejectUnauthorized: false`. The latter accepts
any certificate, which defeats TLS against an active attacker.

All three support **Gateway** routing and **platform-managed credentials**.

### The connection user's privileges

The connection user must be able to do whatever the consuming feature needs:

| Consumer | The connection user must be able to |
|----------|-----------------------------------|
| SQL credentials rotation | `ALTER USER` on the two rotated accounts |
| SQL dynamic secrets | `CREATE ROLE` / `CREATE USER`, `GRANT`, `DROP` |

A read-only connection user cannot drive either feature. Managed database services sometimes
restrict `ALTER USER` on other accounts even for the admin user — verify before promising a
rotation will work.

## Other databases

| Connection | Slug | Method | Notes |
|------------|------|--------|-------|
| OracleDB | `oracledb` | see docs | Credentials supplied directly |
| MongoDB | `mongodb` | `username-and-password` | |
| Redis | `redis` | `username-and-password` | Redis 6+ for ACL users |
| Snowflake | `snowflake` | `username-and-token` | Username plus a token, not a password |

## LDAP — `ldap`

Method: `simple-bind`.

```json
{
  "name": "corp-ldap",
  "method": "simple-bind",
  "credentials": {
    "provider": "active-directory",
    "url": "ldaps://dc1.corp.example.com:636",
    "dn": "CN=infisical,OU=Service Accounts,DC=corp,DC=example,DC=com",
    "password": "...",
    "sslRejectUnauthorized": true,
    "sslCertificate": "-----BEGIN CERTIFICATE-----\n..."
  },
  "gatewayId": "<gateway-uuid>"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `provider` | Yes | Directory flavor |
| `url` | Yes | Use `ldaps://` in production |
| `dn` | Yes | Bind DN — the full distinguished name, not a bare username |
| `password` | Yes | Bind password |
| `sslRejectUnauthorized` | No | |
| `sslCertificate` | No | CA certificate |

Supports Gateway routing **and** connection credential rotation — Infisical can rotate its own bind
password on a schedule.

The bind account's rights determine what LDAP features work: an `ldap-password` rotation with
`rotationMethod: connection-principal` needs password-reset rights over the target entries. See
`infisical-secret-rotation`.

## SSH — `ssh`

Methods: `password`, `ssh-key`.

```json
{
  "method": "ssh-key",
  "credentials": {
    "host": "bastion.internal.example.com",
    "port": 22,
    "username": "infisical",
    "privateKey": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
    "passphrase": "<optional>"
  },
  "gatewayId": "<gateway-uuid>"
}
```

| Method | Fields |
|--------|--------|
| `password` | `host`, `port`, `username`, `password` |
| `ssh-key` | `host`, `port`, `username`, `privateKey`, `passphrase` (optional) |

Consumed by the `unix-linux-local-account` and `hp-ilo-local-account` rotations. Prefer `ssh-key`.

## Windows — `smb` and `winrm`

Two separate connections for Windows, used by different features.

### `smb` — method `credentials`

```json
{
  "method": "credentials",
  "credentials": {
    "host": "fileserver.corp.example.com",
    "port": 445,
    "domain": "CORP",
    "username": "svc_infisical",
    "password": "..."
  }
}
```

Consumed by the `windows-local-account` rotation. Supports Gateway routing.

### `winrm` — method `username-password`

Note: `username-password`, **not** `username-and-password`.

```json
{
  "method": "username-password",
  "credentials": {
    "host": "win-host.corp.example.com",
    "port": 5986,
    "username": "svc_infisical",
    "password": "...",
    "sslEnabled": true,
    "sslRejectUnauthorized": true,
    "sslCertificate": "-----BEGIN CERTIFICATE-----\n..."
  }
}
```

Supports Gateway routing. Use port 5986 with `sslEnabled: true`; 5985 is plaintext HTTP.

## Certificate services and load balancers

| Connection | Slug | Method | Used by |
|------------|------|--------|---------|
| Azure ADCS (Web Enrollment) | `azure-adcs` | `username-password` | PKI external CA |
| Microsoft ADCS | `adcs` | `username-password` | PKI external CA |
| Venafi TLS Protect Cloud | `venafi` | `api-key` | PKI external CA |
| Venafi TPP | `venafi-tpp` | `oauth` | PKI external CA |
| DigiCert | `digicert` | `api-key` | PKI external CA |
| NetScaler | `netscaler` | `basic-auth` | PKI certificate sync |
| F5 BIG-IP | `f5-big-ip` | `basic-auth` | PKI certificate sync |
| Kemp LoadMaster | `kemp-loadmaster` | `basic-auth` | PKI certificate sync |
| Nutanix Prism Central | `nutanix-prism-central` | `api-key`, `basic-auth` | PKI certificate sync |
| Microsoft Intune | `microsoft-intune` | `client-secret` | PKI enrollment |

`adcs`, `azure-adcs`, `venafi-tpp`, `netscaler`, `f5-big-ip`, `kemp-loadmaster`, and
`nutanix-prism-central` support Gateway routing — they are typically internal. See `infisical-pki`.

## Gateway routing

Only these **16** connection types accept `gatewayId` / `gatewayPoolId`:

`adcs`, `azure-key-vault`, `f5-big-ip`, `github`, `hashicorp-vault`, `kemp-loadmaster`, `ldap`,
`mssql`, `mysql`, `netscaler`, `nutanix-prism-central`, `postgres`, `smb`, `ssh`, `venafi-tpp`,
`winrm`

Rules:

- Passing `gatewayId` to any other connection type is a **validation error**: `Not supported for <Name> Connections`
- `gatewayId` and `gatewayPoolId` are mutually exclusive — `Cannot specify both a gateway and a gateway pool`
- The Gateway must already exist and be healthy

Use a gateway when the target has no public endpoint — a VPC-only RDS instance, an internal domain
controller, an on-premises ADCS server. See `infisical-gateway` for deployment.

If a user needs to reach a private service whose connection type is **not** in the list above, a
gateway will not help; they need network-level reachability instead.

## Platform-managed credentials

Only `postgres`, `mysql`, and `mssql` support `isPlatformManagedCredentials: true`.

Infisical takes ownership of the database password and manages it itself, so you stop hand-syncing
a credential between the database and Infisical.

**Do not enable it on an account shared with humans or other systems.** Infisical will change the
password, and everything else using that account breaks.
