# Provider Setup & Authentication

Configure the Infisical Terraform Provider with the correct authentication method for your environment.

## Provider Source Block

All Terraform configurations using Infisical must specify the official provider from Terraform Registry:

```hcl
terraform {
  required_providers {
    infisical = {
      source = "infisical/infisical"
      # Pin a version for reproducible plans; check the registry for the current release.
    }
  }
}

provider "infisical" {
  host = "https://app.infisical.com" # Optional for cloud, required for self-hosted

  auth = {
    # Exactly one of `universal` or `oidc` (see below)
  }
}
```

> **Critical:** credentials go inside a nested `auth = { ... }` attribute, keyed by method.
> Setting `client_id`/`client_secret`/`identity_id` directly on the provider block is not valid
> for this provider and will fail with an unsupported-argument error.

## Authentication Methods

### 1. Universal Auth (Recommended for Most Use Cases)

Universal Auth uses a `client_id` and `client_secret` to authenticate the provider. This is the most straightforward method for local development and self-hosted environments.

**Setup**:
1. In Infisical, create a Machine Identity
2. Attach a Universal Auth method with a client ID and secret
3. Grant the identity appropriate project/org permissions

**HCL Configuration**:

```hcl
provider "infisical" {
  host = "https://app.infisical.com" # Optional for cloud, required for self-hosted

  auth = {
    universal = {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}
```

Or omit the values and let the provider read them from the environment:

```hcl
provider "infisical" {
  # Reads from:
  # - INFISICAL_UNIVERSAL_AUTH_CLIENT_ID
  # - INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET
}
```

**Environment Variables**:

```bash
export INFISICAL_UNIVERSAL_AUTH_CLIENT_ID="your-client-id"
export INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET="your-client-secret"
```

### 2. OIDC (Recommended for Terraform Cloud)

OIDC (OpenID Connect) is the recommended authentication method for CI/CD platforms like Terraform Cloud and CircleCI. It eliminates the need to store long-lived secrets.

**Setup**:
1. In Infisical, create a Machine Identity
2. Add an OIDC Auth method
3. Configure the identity issuer URL and audience
4. In your CI/CD platform, set the `TFC_WORKLOAD_IDENTITY_TOKEN` environment variable

**HCL Configuration**:

```hcl
provider "infisical" {
  host = "https://app.infisical.com"

  auth = {
    oidc = {
      identity_id = var.infisical_identity_id
      # Name of the env var your platform puts the OIDC token in.
      # Set this explicitly to match whatever your CI injects.
      token_environment_variable_name = "INFISICAL_TOKEN"
    }
  }
}
```

Or for Terraform Cloud with automatic token injection:

```hcl
provider "infisical" {
  host = "https://app.infisical.com"

  auth = {
    oidc = {
      identity_id = var.infisical_machine_identity_id
      # Must match the variable Terraform Cloud injects
      token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
    }
  }
}
```

**Terraform Cloud Setup**:
```hcl
# Set in your TFC workspace variables
variable "infisical_machine_identity_id" {
  type = string
  # HCP Terraform will inject: TFC_WORKLOAD_IDENTITY_TOKEN
}

provider "infisical" {
  host = "https://app.infisical.com"

  auth = {
    oidc = {
      identity_id                     = var.infisical_machine_identity_id
      token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
    }
  }
}
```

If you configure multiple workload identity tokens in TFC, point
`token_environment_variable_name` at the specific one you want (e.g.
`TFC_WORKLOAD_IDENTITY_TOKEN_INFISICAL`).

See [Terraform Cloud OIDC Setup](/references/terraform-cloud-oidc.md) for complete step-by-step guide.

### 3. Service Token (Legacy — Do Not Use)

Service tokens are legacy and will be removed in a future release. Use Universal Auth or OIDC instead.

Note the attribute is `service_token`, and unlike machine identity auth it sits at the top level
of the provider block rather than inside `auth`:

```hcl
# ⚠️ LEGACY — Do not use in new configurations
provider "infisical" {
  host          = "https://app.infisical.com"
  service_token = var.infisical_service_token
}
```

## Environment Variables Reference

| Variable | Auth Method | Purpose |
|----------|-------------|---------|
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` | Universal Auth | Client ID for authentication |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` | Universal Auth | Client secret for authentication |
| `INFISICAL_TOKEN` | Legacy | Legacy service token |

For OIDC, the token env var has no fixed name — you name it yourself via
`token_environment_variable_name` inside `auth.oidc`, and it must match what your CI platform
injects.

Instance URL is set with the provider's `host` attribute rather than an environment variable.

## Self-Hosted Configuration

If you're running a self-hosted Infisical instance, you must explicitly set the `host` parameter:

```hcl
provider "infisical" {
  host = "https://infisical.mycompany.com"

  auth = {
    universal = {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}
```

## Cloud Deployment Configuration

For Infisical Cloud (app.infisical.com), the `host` parameter is optional and defaults to the cloud instance. You only need auth credentials:

```hcl
provider "infisical" {
  auth = {
    universal = {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}
```

## Complete Example with Terraform Variables

```hcl
variable "infisical_client_id" {
  type        = string
  description = "Infisical Machine Identity Client ID"
  sensitive   = true
}

variable "infisical_client_secret" {
  type        = string
  description = "Infisical Machine Identity Client Secret"
  sensitive   = true
}

provider "infisical" {
  auth = {
    universal = {
      client_id     = var.infisical_client_id
      client_secret = var.infisical_client_secret
    }
  }
}

# Now you can use Infisical resources
ephemeral "infisical_secret" "db_password" {
  name         = "DB_PASSWORD"
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
}

# Ephemeral values may only flow into other ephemeral contexts — another provider's
# config, a write-only argument, or an output explicitly marked ephemeral.
output "database_password" {
  value     = ephemeral.infisical_secret.db_password.value
  sensitive = true
  ephemeral = true
}
```

## Troubleshooting

**"Error: Unsupported argument" on `client_id` / `client_secret` / `identity_id`**: These belong inside the nested `auth = { universal = {...} }` or `auth = { oidc = {...} }` attribute, not directly on the provider block.

**"Error: Unauthorized"**: Check that your client ID and secret are correct and that the Machine Identity has permissions for the workspace/project you're accessing.

**"Error: identity_id is required for OIDC"**: Ensure you've set `identity_id` inside `auth.oidc` and that `token_environment_variable_name` matches the variable your CI/CD platform actually injects.

**Self-hosted returning 404 or auth failures**: Self-hosted instances require explicit `host` configuration on the provider block.

**"Ephemeral value not allowed here"**: An ephemeral resource's value cannot land in state. Feed it into a provider config, a write-only argument, or an output marked `ephemeral = true`.
