# Using Terraform Ephemeral Resources with Infisical

To fetch secrets from Infisical without storing them in your Terraform state file, use **ephemeral resources** (available in Terraform v1.10+). This approach ensures sensitive values are never persisted and provides enhanced security for GitOps workflows.

## Prerequisites

- Terraform v1.10.0 or later (required for ephemeral resources)
- An Infisical account with access to a project
- Machine Identity credentials (client ID and secret)

## Complete HCL Configuration

### Step 1: Configure the Infisical Provider

```hcl
terraform {
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.1"
    }
  }
  required_version = ">= 1.10.0"
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

### Step 2: Define Input Variables

```hcl
variable "infisical_client_id" {
  description = "Infisical Machine Identity client ID"
  type        = string
  sensitive   = true
}

variable "infisical_client_secret" {
  description = "Infisical Machine Identity client secret"
  type        = string
  sensitive   = true
}

variable "infisical_workspace_id" {
  description = "Infisical workspace ID"
  type        = string
}
```

### Step 3: Declare Ephemeral Resources

```hcl
# Fetch a single secret
ephemeral "infisical_secret" "db_credentials" {
  name         = "DB_CREDENTIALS"
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/database"
}

# Fetch another secret from a different path
ephemeral "infisical_secret" "api_key" {
  name         = "API_KEY"
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/api"
}

# Fetch all secrets from a folder
ephemeral "infisical_secret" "all_secrets" {
  env_slug     = "prod"
  workspace_id = var.infisical_workspace_id
  folder_path  = "/app"
}
```

### Step 4: Use Ephemeral Secrets in Resources

```hcl
# Example: Configure PostgreSQL provider with fetched credentials
provider "postgresql" {
  host     = "db.example.com"
  port     = 5432
  username = jsondecode(ephemeral.infisical_secret.db_credentials.value)["username"]
  password = jsondecode(ephemeral.infisical_secret.db_credentials.value)["password"]
  database = "myapp"
  sslmode  = "require"
}

# Example: Create RDS database with secret rotation
resource "aws_db_instance" "example" {
  identifier     = "myapp-db"
  engine         = "postgres"
  instance_class = "db.t3.medium"
  username       = jsondecode(ephemeral.infisical_secret.db_credentials.value)["username"]
  password       = jsondecode(ephemeral.infisical_secret.db_credentials.value)["password"]
  allocated_storage = 20
  
  lifecycle {
    ignore_changes = [password]
  }
}

# Example: Pass secrets to environment variables
resource "null_resource" "app_deployment" {
  triggers = {
    api_key = ephemeral.infisical_secret.api_key.value
  }
  
  provisioner "local-exec" {
    command = "echo 'Deploying app...'"
    environment = {
      API_KEY = ephemeral.infisical_secret.api_key.value
    }
  }
}
```

## Complete Example: Multi-Environment Setup

```hcl
# variables.tf
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "infisical_client_id" {
  type      = string
  sensitive = true
}

variable "infisical_client_secret" {
  type      = string
  sensitive = true
}

variable "infisical_workspace_id" {
  type = string
}

# main.tf
terraform {
  required_providers {
    infisical = {
      source = "infisical/infisical"
    }
  }
  required_version = ">= 1.10.0"
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

# Fetch secrets for the current environment
ephemeral "infisical_secret" "db_password" {
  name         = "DB_PASSWORD"
  env_slug     = var.environment
  workspace_id = var.infisical_workspace_id
  folder_path  = "/database"
}

ephemeral "infisical_secret" "jwt_secret" {
  name         = "JWT_SECRET"
  env_slug     = var.environment
  workspace_id = var.infisical_workspace_id
  folder_path  = "/auth"
}

# Use in local_exec provisioner or any resource
output "deployment_status" {
  value = "Secrets fetched without persisting to state"
}
```

## Key Advantages

| Feature | Ephemeral Resources | Data Sources (Legacy) |
|---------|-------------------|----------------------|
| **State File Storage** | ❌ Never stored | ❌ Stored in plaintext |
| **Sensitive Exposure Risk** | ✅ None | ❌ High |
| **GitOps Compatible** | ✅ Yes | ❌ No |
| **Terraform Version** | v1.10+ | All versions |
| **Recommended** | ✅ Yes | ❌ Deprecated |

## Deployment with Variables

Create a `terraform.tfvars` file (add to `.gitignore`):

```hcl
infisical_client_id     = "your-machine-identity-client-id"
infisical_client_secret = "your-machine-identity-client-secret"
infisical_workspace_id  = "your-workspace-id"
environment             = "prod"
```

Run Terraform:

```bash
terraform init
terraform plan
terraform apply
```

## Security Best Practices

1. **Use Machine Identity** — Never use service tokens; they're legacy and deprecated
2. **Mark Variables as Sensitive** — Prevents accidental output of credentials
3. **Never Commit Credentials** — Add `terraform.tfvars` and `.terraform/` to `.gitignore`
4. **Rotate Credentials Regularly** — Periodically update Machine Identity secrets in Infisical
5. **Audit Access** — Monitor who fetches secrets via Terraform logs and Infisical audit trails
6. **Use Environment Variables** — For CI/CD, set variables via `TF_VAR_*` environment variables:
   ```bash
   export TF_VAR_infisical_client_id="..."
   export TF_VAR_infisical_client_secret="..."
   ```

## Troubleshooting

**Error: Ephemeral resources not supported**
- Ensure Terraform >= v1.10.0: `terraform version`

**Error: Invalid credentials**
- Verify Machine Identity client ID and secret are correct
- Check that the Machine Identity has access to the workspace

**Error: Secret not found**
- Confirm `name`, `env_slug`, `folder_path`, and `workspace_id` match your Infisical setup
- Verify the secret exists in Infisical UI under the specified path

**Secrets appearing in state file**
- If using data sources instead of ephemeral resources, migrate to ephemeral resources
- Never commit `.tfstate` files to version control
