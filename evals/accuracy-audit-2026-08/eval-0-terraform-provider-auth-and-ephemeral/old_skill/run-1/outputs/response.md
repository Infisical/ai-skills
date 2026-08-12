Here's a complete configuration using Universal Auth for the provider and an `ephemeral` resource so `DATABASE_PASSWORD` never gets written to state (requires Terraform 1.10+).

```hcl
terraform {
  required_version = ">= 1.10"

  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.13"
    }
  }
}

variable "infisical_client_id" {
  type        = string
  description = "Infisical Machine Identity Client ID (Universal Auth)"
  sensitive   = true
}

variable "infisical_client_secret" {
  type        = string
  description = "Infisical Machine Identity Client Secret (Universal Auth)"
  sensitive   = true
}

variable "infisical_workspace_id" {
  type        = string
  description = "Infisical project/workspace ID"
}

provider "infisical" {
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
  # host = "https://infisical.mycompany.com" # only needed for self-hosted
}

ephemeral "infisical_secret" "db_password" {
  workspace_id = var.infisical_workspace_id
  env_slug     = "prod"
  secret_key   = "DATABASE_PASSWORD"
  folder_path  = "/"
}

# Example consumption: pass the ephemeral value straight into a resource/provider
# without ever assigning it to a persisted output or a non-ephemeral variable.
resource "aws_db_instance" "main" {
  allocated_storage   = 20
  engine              = "postgres"
  engine_version      = "15.4"
  instance_class      = "db.t3.micro"
  username            = "admin"
  password            = ephemeral.infisical_secret.db_password.value
  skip_final_snapshot = true
}
```

Run it with credentials supplied via environment variables instead of a `.tfvars` file, so the secret material doesn't sit in a plan/apply command history or get accidentally committed:

```bash
export INFISICAL_UNIVERSAL_AUTH_CLIENT_ID="your-client-id"
export INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET="your-client-secret"
export TF_VAR_infisical_workspace_id="your-workspace-id"

terraform init
terraform apply
```

Notes on why it's built this way:

- `ephemeral` (not `data "infisical_secrets"`) is what keeps `DATABASE_PASSWORD` out of the state file entirely, per the skill's core guidance. If you instead output it via `output "..." { value = ephemeral.infisical_secret.db_password.value }`, Terraform will reject it since ephemeral values can't flow into persisted outputs, resource attributes are fine.
- Universal Auth (`client_id`/`client_secret`) is used since this looks like local or self-hosted usage. If this is destined for Terraform Cloud, swap the provider block for OIDC with `identity_id` and `token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"` instead, that's the recommended pattern there.
- Do not use the deprecated `token` (Service Token) auth method.
