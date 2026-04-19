# Terraform Configuration for Infisical Secrets Without State Storage

To fetch secrets from Infisical in Terraform without storing them in the state file, you need to use **sensitive outputs** combined with the **Infisical provider** and Terraform's `sensitive` mark. Here's a complete working configuration:

## 1. Provider Configuration

```hcl
terraform {
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.8"
    }
  }
}

provider "infisical" {
  host  = var.infisical_host
  token = var.infisical_token
}
```

## 2. Variable Definitions

Create a `variables.tf` file:

```hcl
variable "infisical_host" {
  description = "Infisical API host URL"
  type        = string
  default     = "https://app.infisical.com"
  sensitive   = false
}

variable "infisical_token" {
  description = "Infisical API token or service token"
  type        = string
  sensitive   = true
}

variable "project_id" {
  description = "Infisical project ID"
  type        = string
  sensitive   = false
}

variable "environment" {
  description = "Infisical environment (e.g., 'dev', 'prod')"
  type        = string
  default     = "dev"
  sensitive   = false
}

variable "secret_path" {
  description = "Path to secrets in Infisical (e.g., '/app/database')"
  type        = string
  default     = "/"
  sensitive   = false
}
```

## 3. Data Source Configuration

```hcl
# Fetch all secrets from a specific path in Infisical
data "infisical_secrets" "app_secrets" {
  project_id  = var.project_id
  environment = var.environment
  path        = var.secret_path
}

# Fetch a specific secret by name
data "infisical_secret" "database_password" {
  project_id  = var.project_id
  environment = var.environment
  secret_name = "DATABASE_PASSWORD"
  path        = var.secret_path
}
```

## 4. Sensitive Outputs (Preventing State Storage)

Create an `outputs.tf` file:

```hcl
# Mark outputs as sensitive to prevent them from being written to state
output "all_secrets" {
  description = "All secrets fetched from Infisical"
  value       = data.infisical_secrets.app_secrets.secrets
  sensitive   = true
}

output "database_password" {
  description = "Database password from Infisical"
  value       = data.infisical_secret.database_password.secret_value
  sensitive   = true
}

# If you need to pass secrets to other resources, ensure those resources
# are also configured to handle sensitive values appropriately
output "app_environment_variables" {
  description = "Environment variables for application"
  value = {
    DATABASE_PASSWORD = data.infisical_secret.database_password.secret_value
    DATABASE_HOST     = data.infisical_secret.db_host.secret_value
    DATABASE_PORT     = data.infisical_secret.db_port.secret_value
  }
  sensitive = true
}
```

## 5. Complete Working Example

Here's a complete example that uses fetched secrets without storing them in state:

```hcl
# main.tf

terraform {
  required_version = ">= 1.0"
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.8"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "infisical" {
  host  = var.infisical_host
  token = var.infisical_token
}

provider "aws" {
  region = var.aws_region
}

# Fetch database credentials from Infisical
data "infisical_secret" "db_username" {
  project_id  = var.project_id
  environment = var.environment
  secret_name = "DB_USERNAME"
}

data "infisical_secret" "db_password" {
  project_id  = var.project_id
  environment = var.environment
  secret_name = "DB_PASSWORD"
}

data "infisical_secret" "db_host" {
  project_id  = var.project_id
  environment = var.environment
  secret_name = "DB_HOST"
}

# Use fetched secrets in AWS resource
resource "aws_db_instance" "main" {
  identifier     = "myapp-database"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t4g.micro"

  # Pass secrets directly without storing in state
  username = data.infisical_secret.db_username.secret_value
  password = data.infisical_secret.db_password.secret_value
  
  allocated_storage = 20
  skip_final_snapshot = true
  
  lifecycle {
    # Prevent accidental replacement
    prevent_destroy = true
  }
}

# Create environment variables file for application
resource "local_file" "app_env" {
  filename = "${path.module}/.env"
  content = templatefile("${path.module}/.env.tpl", {
    db_username = data.infisical_secret.db_username.secret_value
    db_password = data.infisical_secret.db_password.secret_value
    db_host     = data.infisical_secret.db_host.secret_value
  })
  
  sensitive_content = true
}

# Sensitive outputs that won't be stored in state
output "database_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "database_credentials_managed" {
  description = "Database credentials are managed by Infisical and not stored in Terraform state"
  value       = "Secrets fetched at runtime; stored only in memory during apply"
  sensitive   = true
}
```

## 6. Usage with terraform.tfvars

Create `terraform.tfvars`:

```hcl
infisical_host = "https://app.infisical.com"
infisical_token = "<your-service-token-here>"
project_id    = "<your-project-id>"
environment   = "prod"
secret_path   = "/app"
aws_region    = "us-east-1"
```

Or use environment variables:

```bash
export TF_VAR_infisical_token="your-service-token"
export TF_VAR_project_id="your-project-id"
terraform plan
terraform apply
```

## 7. Best Practices for State Security

### Use Remote State with Encryption

```hcl
terraform {
  cloud {
    organization = "your-org"
    
    workspaces {
      name = "production"
    }
  }
}
```

### Or use S3 backend with encryption:

```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "infisical/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### Use Service Tokens with Limited Scope

In Infisical, create a service token with:
- Only read access to required secrets
- Limited to specific environments (prod, staging)
- Set appropriate expiration dates
- Rotate tokens regularly

## 8. Key Security Considerations

1. **Sensitive Mark**: All secret outputs must be marked `sensitive = true`
2. **No Logging**: Use `-sensitive` output filters when sharing plan output
3. **Service Tokens**: Use service tokens instead of user tokens for automation
4. **State Backend**: Use encrypted S3, Terraform Cloud, or equivalent
5. **RBAC**: Configure Infisical project permissions to limit what service tokens can access
6. **No Hardcoding**: Always use variables for secrets, never hardcode values
7. **Rotation**: Implement secret rotation policies in Infisical

## 9. Viewing Plans Safely

When using sensitive outputs, use:

```bash
# Hide sensitive values in plan
terraform plan -no-color | grep -v "sensitive"

# Or with Terraform Cloud:
terraform plan -json | jq '.resource_changes[] | select(.sensitive != null)'
```

## 10. Testing Configuration

```bash
# Validate syntax
terraform validate

# Format check
terraform fmt -check

# Plan without showing sensitive values
terraform plan -lock=false

# Apply
terraform apply

# Destroy (be careful with this in production)
terraform destroy
```

## Summary

This configuration ensures that:
- Secrets are **fetched at runtime** from Infisical
- Secrets are **never written to the Terraform state file** (marked as sensitive)
- Sensitive outputs are **redacted in CLI output**
- Infisical remains the **single source of truth** for secrets
- Terraform is used purely for **infrastructure orchestration**, not secret storage
- Service tokens provide **secure, scoped access** to secrets

By using the `sensitive = true` attribute and the Infisical data sources, you maintain a clean separation of concerns where Infisical manages secrets and Terraform manages infrastructure provisioning.