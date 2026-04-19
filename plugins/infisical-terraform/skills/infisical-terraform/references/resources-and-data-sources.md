# Resources & Data Sources

Guide to Infisical Terraform resources and data sources for managing secrets, roles, and access policies.

## Ephemeral Resource: infisical_secret

The `ephemeral` resource is the **recommended way** to fetch secrets in Terraform 1.10+. Secret values are **never stored in state**.

**Key Benefit**: Prevents secrets from being persisted in your Terraform state files, reducing security risk.

**Requires**: Terraform 1.10 or later.

### Configuration

```hcl
ephemeral "infisical_secret" "example" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  secret_key   = "DATABASE_PASSWORD"
  folder_path  = "/" # Optional, defaults to "/"
}

output "db_password" {
  value     = ephemeral.infisical_secret.example.value
  sensitive = true
}
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `workspace_id` | string | ID of the Infisical workspace |
| `env_slug` | string | Environment slug (e.g., "dev", "staging", "prod") |
| `secret_key` | string | Name of the secret to retrieve |
| `folder_path` | string | Path within the environment (optional, defaults to "/") |
| `value` | string (computed) | The secret value (only available during apply, never stored in state) |

### JSON Secrets

For JSON-formatted secrets, use `jsondecode()` to parse the value:

```hcl
ephemeral "infisical_secret" "api_config" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  secret_key   = "API_CONFIG"
}

locals {
  config = jsondecode(ephemeral.infisical_secret.api_config.value)
}

output "api_key" {
  value     = local.config.api_key
  sensitive = true
}

output "api_url" {
  value = local.config.api_url
}
```

### Usage with Resources

```hcl
# Fetch secret and use it to configure a provider
ephemeral "infisical_secret" "aws_access_key" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  secret_key   = "AWS_ACCESS_KEY_ID"
}

ephemeral "infisical_secret" "aws_secret_key" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  secret_key   = "AWS_SECRET_ACCESS_KEY"
}

provider "aws" {
  access_key = ephemeral.infisical_secret.aws_access_key.value
  secret_key = ephemeral.infisical_secret.aws_secret_key.value
  region     = "us-east-1"
}
```

---

## Data Source: infisical_secrets

The `data` source retrieves all secrets from a specific environment and folder. **⚠️ Warning**: Secret values **ARE stored in Terraform state**. Use `ephemeral` instead when possible.

### Configuration

```hcl
data "infisical_secrets" "all_secrets" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  folder_path  = "/" # Optional, defaults to "/"
}

output "all_secrets" {
  value     = data.infisical_secrets.all_secrets.secrets
  sensitive = true
}
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `workspace_id` | string | ID of the Infisical workspace |
| `env_slug` | string | Environment slug |
| `folder_path` | string | Path within the environment (optional, defaults to "/") |
| `secrets` | map(string) | Map of all secrets in the folder (key → value) |

### Usage Example

```hcl
data "infisical_secrets" "all_secrets" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
}

# Access individual secrets
output "database_password" {
  value     = data.infisical_secrets.all_secrets.secrets["DB_PASSWORD"]
  sensitive = true
}

# Use secrets in resource configuration
resource "aws_db_instance" "main" {
  allocated_storage    = 100
  engine               = "postgres"
  engine_version       = "15.2"
  instance_class       = "db.t3.micro"
  username             = "admin"
  password             = data.infisical_secrets.all_secrets.secrets["DB_PASSWORD"]
  skip_final_snapshot  = true
}
```

---

## Resource: infisical_project_role

Create and manage custom project roles with granular permissions.

### Permissions v2 Format (Recommended)

Use `permissions_v2` for modern, flexible permission definitions with subject-action structure.

```hcl
resource "infisical_project_role" "developer" {
  project_id = "your-project-id"
  name       = "Developer"

  permissions_v2 = [
    {
      subject = "secrets"
      actions = ["read", "create", "edit"]
    },
    {
      subject = "secret-folders"
      actions = ["read", "create", "edit"]
    },
    {
      subject = "secret-imports"
      actions = ["read"]
    },
    {
      subject = "dynamic-secrets"
      actions = ["read", "lease"]
    }
  ]
}
```

### Permissions v2 Subjects & Actions

| Subject | Available Actions |
|---------|-------------------|
| `secrets` | read, create, edit, delete, read-metadata |
| `secret-folders` | read, create, edit, delete |
| `secret-imports` | read, create, edit, delete |
| `dynamic-secrets` | read, read-root-credential, create-root-credential, edit-root-credential, delete-root-credential, lease |

### Permissions v1 Format (Deprecated)

The old `permissions` attribute uses inverted logic (denying actions). It's deprecated—always prefer `permissions_v2`.

```hcl
# ⚠️ DEPRECATED — Do not use in new code
resource "infisical_project_role" "viewer" {
  project_id = "your-project-id"
  name       = "Viewer"

  permissions = [
    {
      action   = "create"
      inverted = true
    },
    {
      action   = "edit"
      inverted = true
    },
    {
      action   = "delete"
      inverted = true
    }
  ]
}
```

### Complete Example with Multiple Roles

```hcl
resource "infisical_project_role" "admin" {
  project_id = "your-project-id"
  name       = "Admin"

  permissions_v2 = [
    {
      subject = "secrets"
      actions = ["read", "create", "edit", "delete"]
    },
    {
      subject = "secret-folders"
      actions = ["read", "create", "edit", "delete"]
    },
    {
      subject = "secret-imports"
      actions = ["read", "create", "edit", "delete"]
    },
    {
      subject = "dynamic-secrets"
      actions = ["read", "read-root-credential", "create-root-credential", "edit-root-credential", "delete-root-credential", "lease"]
    }
  ]
}

resource "infisical_project_role" "ops" {
  project_id = "your-project-id"
  name       = "Ops"

  permissions_v2 = [
    {
      subject = "secrets"
      actions = ["read"]
    },
    {
      subject = "dynamic-secrets"
      actions = ["read", "lease"]
    }
  ]
}
```

---

## Resource: infisical_access_approval_policy

Enforce approval workflows for sensitive secret operations.

### Configuration

```hcl
resource "infisical_access_approval_policy" "prod_secrets" {
  project_id      = "your-project-id"
  name            = "Production Secrets Approval"
  environment_slug = "prod"
  secret_path     = "/" # Optional, specific path or "/" for all

  approvers = [
    {
      type     = "username"
      username = "alice@company.com"
    },
    {
      type     = "username"
      username = "bob@company.com"
    }
  ]

  required_approvals = 1
  enforcement_level  = "hard" # "soft" (warning) or "hard" (blocking)
}
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `project_id` | string | ID of the Infisical project |
| `name` | string | Policy name for identification |
| `environment_slug` | string | Environment to apply policy (e.g., "prod") |
| `secret_path` | string | Secret path (optional, "/" for all secrets) |
| `approvers` | list(object) | List of approvers with `type` and `username` |
| `required_approvals` | number | Number of approvals required before access granted |
| `enforcement_level` | string | "soft" (warning) or "hard" (blocking access without approval) |

### Example: Multiple Approval Policies

```hcl
# Require approval for all production secrets
resource "infisical_access_approval_policy" "prod_all" {
  project_id       = "your-project-id"
  name             = "Production - All Secrets"
  environment_slug = "prod"
  secret_path      = "/"

  approvers = [
    {
      type     = "username"
      username = "security-lead@company.com"
    },
    {
      type     = "username"
      username = "ops-manager@company.com"
    }
  ]

  required_approvals = 2
  enforcement_level  = "hard"
}

# Require approval for database secrets only
resource "infisical_access_approval_policy" "prod_database" {
  project_id       = "your-project-id"
  name             = "Production - Database Secrets"
  environment_slug = "prod"
  secret_path      = "/database"

  approvers = [
    {
      type     = "username"
      username = "dba@company.com"
    }
  ]

  required_approvals = 1
  enforcement_level  = "hard"
}
```

---

## Complete Example: Secrets + Roles + Approvals

```hcl
terraform {
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.13"
    }
  }
}

provider "infisical" {
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
}

variable "infisical_client_id" {
  type      = string
  sensitive = true
}

variable "infisical_client_secret" {
  type      = string
  sensitive = true
}

# Fetch production database password (never in state)
ephemeral "infisical_secret" "db_password" {
  workspace_id = "ws-abc123"
  env_slug     = "prod"
  secret_key   = "DATABASE_PASSWORD"
}

# Define developer role with permission to read secrets
resource "infisical_project_role" "developer" {
  project_id = "proj-xyz789"
  name       = "Developer"

  permissions_v2 = [
    {
      subject = "secrets"
      actions = ["read"]
    }
  ]
}

# Require approval for production secret access
resource "infisical_access_approval_policy" "prod_approval" {
  project_id       = "proj-xyz789"
  name             = "Production Approval"
  environment_slug = "prod"
  secret_path      = "/"

  approvers = [
    {
      type     = "username"
      username = "security-lead@company.com"
    }
  ]

  required_approvals = 1
  enforcement_level  = "hard"
}

output "database_password" {
  value     = ephemeral.infisical_secret.db_password.value
  sensitive = true
}
```
