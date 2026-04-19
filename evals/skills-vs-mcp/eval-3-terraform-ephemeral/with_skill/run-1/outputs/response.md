# Fetching Infisical Secrets with Terraform Ephemeral Resources

You can use Terraform 1.10+ ephemeral resources to fetch secrets from Infisical without storing them in the state file. This is the recommended approach for handling sensitive data securely.

## Why Ephemeral Resources?

Ephemeral resources ensure that secret values **never persist in your Terraform state file**—they're only available during the current Terraform run. This eliminates the risk of state file exposure.

## Complete HCL Configuration

### 1. Provider Setup

```hcl
terraform {
  required_version = ">= 1.10"
  required_providers {
    infisical = {
      source = "infisical/infisical"
    }
  }
}

provider "infisical" {
  host = "https://app.infisical.com"
  auth {
    universal {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}
```

### 2. Input Variables

```hcl
variable "infisical_client_id" {
  description = "Infisical Machine Identity Client ID"
  type        = string
  sensitive   = true
}

variable "infisical_client_secret" {
  description = "Infisical Machine Identity Client Secret"
  type        = string
  sensitive   = true
}

variable "infisical_workspace_id" {
  description = "Infisical Workspace ID"
  type        = string
}
```

### 3. Ephemeral Secret Resources

```hcl
# Fetch a single secret
ephemeral "infisical_secret" "database_password" {
  name              = "DATABASE_PASSWORD"
  env_slug          = "prod"
  workspace_id      = var.infisical_workspace_id
  folder_path       = "/database"
}

# Fetch another secret
ephemeral "infisical_secret" "api_key" {
  name              = "API_KEY"
  env_slug          = "prod"
  workspace_id      = var.infisical_workspace_id
  folder_path       = "/integrations"
}

# Fetch a secret from the root folder (optional—folder_path defaults to "/")
ephemeral "infisical_secret" "master_key" {
  name              = "MASTER_KEY"
  env_slug          = "prod"
  workspace_id      = var.infisical_workspace_id
}
```

### 4. Using Secrets in Resources

Ephemeral values can be accessed within resource configurations using `ephemeral.TYPE.NAME.value`:

```hcl
resource "aws_db_instance" "main" {
  identifier       = "my-database"
  engine           = "postgres"
  engine_version   = "15.3"
  instance_class   = "db.t4g.micro"
  allocated_storage = 20

  username = "admin"
  password = ephemeral.infisical_secret.database_password.value

  skip_final_snapshot = true
}

resource "aws_ssm_parameter" "api_key" {
  name  = "/app/api-key"
  type  = "SecureString"
  value = ephemeral.infisical_secret.api_key.value
}
```

### 5. Complete Example Terraform File

Here's a working example that integrates all pieces:

```hcl
terraform {
  required_version = ">= 1.10"
  required_providers {
    infisical = {
      source = "infisical/infisical"
    }
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "infisical" {
  host = "https://app.infisical.com"
  auth {
    universal {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "infisical_client_id" {
  description = "Infisical Machine Identity Client ID"
  type        = string
  sensitive   = true
}

variable "infisical_client_secret" {
  description = "Infisical Machine Identity Client Secret"
  type        = string
  sensitive   = true
}

variable "infisical_workspace_id" {
  description = "Infisical Workspace ID"
  type        = string
}

# Fetch database credentials
ephemeral "infisical_secret" "db_password" {
  name              = "DB_PASSWORD"
  env_slug          = "prod"
  workspace_id      = var.infisical_workspace_id
  folder_path       = "/database"
}

ephemeral "infisical_secret" "db_username" {
  name              = "DB_USERNAME"
  env_slug          = "prod"
  workspace_id      = var.infisical_workspace_id
  folder_path       = "/database"
}

# Use secrets in AWS resource
resource "aws_db_instance" "production" {
  identifier           = "prod-db"
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t4g.micro"
  allocated_storage    = 100
  storage_encrypted    = true

  username = ephemeral.infisical_secret.db_username.value
  password = ephemeral.infisical_secret.db_password.value

  skip_final_snapshot = false
  final_snapshot_identifier = "prod-db-final-snapshot"
}

output "database_endpoint" {
  value       = aws_db_instance.production.endpoint
  description = "Database endpoint (secrets not stored in state)"
}
```

## Key Security Features

| Feature | Benefit |
|---------|---------|
| **Ephemeral values** | Never written to `.tfstate` file |
| **Machine Identity auth** | No deprecated Service Tokens; uses Universal Auth (client ID/secret) or OIDC |
| **Sensitive variables** | Input variables marked as `sensitive = true` to mask in logs |
| **No state leakage** | Secret values only available during Terraform execution |

## Running Terraform

```bash
# Set environment variables for credentials
export TF_VAR_infisical_client_id="your-client-id"
export TF_VAR_infisical_client_secret="your-client-secret"
export TF_VAR_infisical_workspace_id="your-workspace-id"

# Plan (secrets fetched, not stored)
terraform plan

# Apply (secrets used, then discarded)
terraform apply
```

## Important Notes

1. **Ephemeral resources are Terraform 1.10+** — Upgrade if you're on an older version.
2. **Values are available only during execution** — Once Terraform finishes, ephemeral values are discarded. They cannot be referenced in outputs or stored for later use.
3. **Machine Identity required** — Create a Machine Identity in Infisical with appropriate permissions for the secrets you need to fetch.
4. **Folder path defaults to "/"** — If omitted, Infisical will search the root folder. Always specify `folder_path` to be explicit about secret location.

## Terraform Cloud / Enterprise OIDC Pattern

For Terraform Cloud, use OIDC instead of client credentials:

```hcl
provider "infisical" {
  host = "https://app.infisical.com"
  auth {
    oidc {
      identity_id = var.infisical_identity_id
    }
  }
}

variable "infisical_identity_id" {
  description = "Infisical OIDC Identity ID"
  type        = string
}
```

This eliminates the need to store client secrets in Terraform Cloud variables.

## Summary

Ephemeral resources with Infisical provide:
- ✅ **Zero state file risk** — Secrets never persisted
- ✅ **Secure authentication** — Machine Identity with Universal Auth or OIDC
- ✅ **Clean separation of concerns** — Secrets fetched on-demand during apply
- ✅ **Production-ready** — Recommended pattern for regulated environments

Use this approach for all sensitive infrastructure configuration managed with Terraform.
