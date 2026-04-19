# Provider Setup & Authentication

Configure the Infisical Terraform Provider with the correct authentication method for your environment.

## Provider Source Block

All Terraform configurations using Infisical must specify the official provider from Terraform Registry:

```hcl
terraform {
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.13" # Use latest stable version
    }
  }
}

provider "infisical" {
  # Auth configuration goes here (see below)
}
```

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
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
}
```

Or use environment variables:

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
  identity_id                   = var.infisical_identity_id
  token_environment_variable_name = "INFISICAL_TOKEN"  # Variable containing OIDC token
}
```

Or for Terraform Cloud with automatic token injection:

```hcl
provider "infisical" {
  identity_id                   = var.infisical_machine_identity_id
  token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
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
  identity_id                   = var.infisical_machine_identity_id
  token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
}
```

See [Terraform Cloud OIDC Setup](/references/terraform-cloud-oidc.md) for complete step-by-step guide.

### 3. Service Token (Deprecated — Do Not Use)

Service tokens are deprecated and should not be used in new configurations. Use Universal Auth or OIDC instead.

```hcl
# ⚠️ DEPRECATED — Do not use
provider "infisical" {
  token = var.infisical_service_token
}
```

## Environment Variables Reference

| Variable | Auth Method | Purpose |
|----------|-------------|---------|
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_ID` | Universal Auth | Client ID for authentication |
| `INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET` | Universal Auth | Client secret for authentication |
| `INFISICAL_TOKEN` | Legacy/Custom | Deprecated service token or custom OIDC token variable |
| `INFISICAL_SITE_URL` | All methods | Custom Infisical instance URL (e.g., `https://infisical.mycompany.com`) |

## Self-Hosted Configuration

If you're running a self-hosted Infisical instance, you must explicitly set the `host` parameter:

```hcl
provider "infisical" {
  host              = "https://infisical.mycompany.com"
  client_id         = var.infisical_client_id
  client_secret     = var.infisical_client_secret
}
```

Or via environment variable:

```bash
export INFISICAL_SITE_URL="https://infisical.mycompany.com"
```

## Cloud Deployment Configuration

For Infisical Cloud (app.infisical.com), the `host` parameter is optional and defaults to the cloud instance. You only need auth credentials:

```hcl
provider "infisical" {
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
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
  client_id     = var.infisical_client_id
  client_secret = var.infisical_client_secret
}

# Now you can use Infisical resources
ephemeral "infisical_secret" "db_password" {
  workspace_id = "your-workspace-id"
  env_slug     = "prod"
  secret_key   = "DB_PASSWORD"
}

output "database_password" {
  value     = ephemeral.infisical_secret.db_password.value
  sensitive = true
}
```

## Troubleshooting

**"Error: Unauthorized"**: Check that your client ID and secret are correct and that the Machine Identity has permissions for the workspace/project you're accessing.

**"Error: identity_id is required for OIDC"**: Ensure you've set the OIDC identity ID and that the token environment variable is properly set in your CI/CD platform.

**"Error: host is required for self-hosted"**: Self-hosted Infisical instances require explicit host configuration. Verify your `INFISICAL_SITE_URL` or `host` parameter.
