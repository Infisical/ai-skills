Building the config now based on the skill's Universal Auth and ephemeral resource patterns.

```hcl
terraform {
  required_version = ">= 1.10"

  required_providers {
    infisical = {
      source = "infisical/infisical"
    }
  }
}

variable "infisical_client_id" {
  type        = string
  description = "Infisical Machine Identity Universal Auth Client ID"
  sensitive   = true
}

variable "infisical_client_secret" {
  type        = string
  description = "Infisical Machine Identity Universal Auth Client Secret"
  sensitive   = true
}

variable "infisical_workspace_id" {
  type        = string
  description = "Infisical project/workspace ID"
}

provider "infisical" {
  host = "https://app.infisical.com" # Optional for Infisical Cloud; required for self-hosted

  auth = {
    universal = {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}

ephemeral "infisical_secret" "database_password" {
  name         = "DATABASE_PASSWORD"
  workspace_id = var.infisical_workspace_id
  env_slug     = "prod"
  folder_path  = "/"
}

output "database_password" {
  value     = ephemeral.infisical_secret.database_password.value
  sensitive = true
  ephemeral = true
}
```

Notes on why this stays out of state:

- The `ephemeral` block (not `data`) is used for `infisical_secret` — its `value` is never written to the state file. This requires Terraform 1.10+.
- Credentials live inside the nested `auth = { universal = { ... } }` attribute, not as top-level provider arguments.
- The secret's key attribute is `name` (not `secret_key`).
- Because the output carries an ephemeral value, it must itself be marked `ephemeral = true`, or Terraform will error since ephemeral values can only flow into other ephemeral contexts.

To run it, supply the two sensitive variables via environment variables (or a `.tfvars` file kept out of version control):

```bash
export TF_VAR_infisical_client_id="..."
export TF_VAR_infisical_client_secret="..."
export TF_VAR_infisical_workspace_id="..."
terraform apply
```

If you'd rather not pass credentials as Terraform variables at all, the provider can also read them straight from `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` / `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` and you can drop the `auth` block's values (keep the empty `universal = {}` to select the method).
