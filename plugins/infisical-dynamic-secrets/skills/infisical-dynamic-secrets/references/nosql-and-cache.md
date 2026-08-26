# Dynamic Secrets: NoSQL & Cache

## Redis

### Prerequisites
- A Redis user with permissions to create ACL users (often the `default` or `admin` user)

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| Secret Name | Yes | Name for this dynamic secret |
| Default TTL | Yes | Default lease duration |
| Max TTL | Yes | Maximum lease duration |
| Host | Yes | Redis hostname or IP address |
| Port | Yes | Redis port (default: `6379`) |
| User | Yes | Admin user (often `default` or `admin`) |
| Password | No | Required if Redis is password-protected |
| CA (SSL) | No | CA certificate (common for managed Redis like AWS ElastiCache, Azure Cache) |

### Redis ACL Statements (Customizable)
Default creates a user with broad access. Customize for least privilege:

```
-- Example: Read-only access to keys with prefix "app:"
ACL SETUSER {{username}} on >{{password}} ~app:* +get +mget +scan +keys
```

**Template variables:** `{{username}}`, `{{password}}`

### Lease Returns
- `DB_USERNAME` — Generated username
- `DB_PASSWORD` — Generated password

### Gotchas
- Requires Redis 6+ with ACL support
- Managed Redis services (Azure Cache) often require SSL — use the CA field
- **For AWS ElastiCache and AWS MemoryDB, use their dedicated providers** (below), not this one — they authenticate through the AWS API rather than a Redis connection

---

## AWS ElastiCache

Provider type: `aws-elasticache`

### Prerequisites
- An AWS IAM principal permitted to manage ElastiCache users and user groups
- The ElastiCache cluster must have RBAC/user-group support enabled

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| `clusterName` | Yes | ElastiCache cluster name |
| `region` | Yes | AWS region of the cluster |
| `auth.type` | Yes | Authentication type |
| `auth.accessKeyId` / `auth.secretAccessKey` | Depends on auth type | AWS credentials |
| `creationStatement` | Yes | Statement Infisical runs to create the user |
| `revocationStatement` | Yes | Statement Infisical runs to remove the user |

### Gotchas
- This provisions ElastiCache **users** via the AWS API, not Redis `ACL SETUSER` commands
- Creation and revocation statements are required — unlike the plain Redis provider, there is no implicit default flow to fall back on

---

## AWS MemoryDB

Provider type: `aws-memorydb`

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| `clusterName` | Yes | MemoryDB cluster name |
| `region` | Yes | AWS region of the cluster |
| `auth.type` | Yes | Authentication type |
| `auth.accessKeyId` / `auth.secretAccessKey` | Depends on auth type | AWS credentials |
| `creationStatement` | Yes | Statement Infisical runs to create the user |
| `revocationStatement` | Yes | Statement Infisical runs to remove the user |
| `host` / `port` | Yes | MemoryDB endpoint |
| `roles` | Yes | Roles/ACL to attach to the generated user |

Same shape as ElastiCache, plus an endpoint and roles.

---

## MongoDB Atlas

Provider type: `mongo-db-atlas`

Atlas uses its own Admin API, not MongoDB commands — this is why it is a separate provider from
plain MongoDB.

### Prerequisites
- An Atlas **API key pair** (public + private) with permission to manage database users in the project

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| `adminPublicKey` | Yes | Atlas API public key |
| `adminPrivateKey` | Yes | Atlas API private key |
| `groupId` | Yes | Atlas **project** ID (Atlas calls this the group ID) |
| `roles` | Yes | Array of roles, each with `roleName`, `databaseName`, and optional `collectionName` |
| `scopes` | No | Restrict the user to specific clusters or data lakes |

### Lease Returns
- `DB_USERNAME` — Generated username
- `DB_PASSWORD` — Generated password

### Gotchas
- `groupId` is the Atlas project ID, which is not the same as the org ID — a common misconfiguration
- Roles are objects (`roleName` + `databaseName`), not plain strings like the self-hosted MongoDB provider

---

## Couchbase

Provider type: `couchbase`

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | Couchbase Capella API URL |
| `orgId` | Yes | Organization ID |
| `projectId` | Yes | Project ID |
| `clusterId` | Yes | Cluster ID |
| `roles` | Yes | Roles to grant the generated user |
| `buckets` | Yes | Buckets the user may access |

---

## Milvus

Provider type: `milvus`

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| `host` | Yes | Milvus host |
| `port` | Yes | Milvus port |
| `username` | Yes | Admin user |
| `password` | Yes | Admin password |
| `database` | Yes | Target database |
| `privileges` | Yes | Array of `{ objectType, objectName, privilege }` grants |

### Gotchas
- Privileges are structured triples, not a flat list — each entry names the object type, the object, and the privilege

---

## MongoDB

Provider type: `mongo-db`

### Prerequisites
- A MongoDB user with `userAdmin` or `userAdminAnyDatabase` role
- **Important:** For MongoDB Atlas, use the separate **MongoDB Atlas** provider documented above — standard MongoDB commands are not supported by Atlas

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| Secret Name | Yes | Name for this dynamic secret |
| Default TTL | Yes | Default lease duration |
| Max TTL | Yes | Maximum lease duration |
| Host | Yes | MongoDB host URL |
| Port | No | Omit if using a cluster/replica set connection string |
| User | Yes | Admin user with userAdmin privileges |
| Password | Yes | Admin user password |
| Database Name | Yes | Target database for the dynamic user |
| Roles | Yes | List of MongoDB roles to assign |
| CA (SSL) | No | CA certificate for TLS connections |

### MongoDB Roles
Built-in roles include:
- `read`, `readWrite` — Database-level
- `dbAdmin`, `dbAdminAnyDatabase` — Admin
- `readAnyDatabase`, `readWriteAnyDatabase` — Cross-database
- `clusterMonitor`, `backup` — Cluster operations
- Custom role names are also supported

### Lease Returns
- `DB_USERNAME` — Generated username
- `DB_PASSWORD` — Generated password

### Gotchas
- **MongoDB vs Atlas:** Use the standard MongoDB provider for self-hosted MongoDB. Use the MongoDB Atlas provider for Atlas clusters — they use different APIs.
- Port is optional because cluster connection strings include the port

---

## Elasticsearch

### Prerequisites
- An Elasticsearch user with privileges to create/delete users and roles

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| Secret Name | Yes | Name for this dynamic secret |
| Default TTL | Yes | Default lease duration |
| Max TTL | Yes | Maximum lease duration |
| Host | Yes | Elasticsearch host URL |
| Port | Yes | Elasticsearch port (default: `9200`) |
| User | Yes | Admin user |
| Password | Yes | Admin user password |
| Roles | Yes | Elasticsearch roles to assign |
| CA (SSL) | No | CA certificate for HTTPS connections |

### Lease Returns
- `DB_USERNAME` — Generated username
- `DB_PASSWORD` — Generated password

---

## RabbitMQ

### Prerequisites
- A RabbitMQ user with administrator tag for management API access

### Configuration
| Field | Required | Description |
|-------|----------|-------------|
| Secret Name | Yes | Name for this dynamic secret |
| Default TTL | Yes | Default lease duration |
| Max TTL | Yes | Maximum lease duration |
| Host | Yes | RabbitMQ management API host |
| Port | Yes | Management API port (default: `15672`) |
| User | Yes | Admin user |
| Password | Yes | Admin user password |
| Virtual Host | Yes | RabbitMQ virtual host |
| Tags | No | User tags (e.g., `monitoring`, `management`) |
| Permissions | No | Configure, write, read regex patterns |

### Lease Returns
- `DB_USERNAME` — Generated username
- `DB_PASSWORD` — Generated password
