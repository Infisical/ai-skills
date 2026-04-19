# Terraform Cloud OIDC Integration

Set up OIDC (OpenID Connect) authentication between Terraform Cloud and Infisical. This is the recommended production pattern for secure, token-free authentication.

## Overview

With OIDC, Terraform Cloud generates a short-lived workload identity token and signs it with a private key. Infisical validates the token against Terraform Cloud's public keys, confirming the identity without storing long-lived secrets. This eliminates the risk of credential leakage and simplifies rotation.

**Key Benefits**:
- No long-lived secrets to rotate
- Automatic token refresh for each Terraform run
- Audit trail of which TFC workspace accessed which secrets
- Compliance-friendly for regulated environments

## Prerequisites

- Infisical workspace with admin access
- Terraform Cloud account with permissions to manage workspaces and variables
- Terraform 1.2+ (for Terraform Cloud workspaces)

## Step 1: Create a Machine Identity in Infisical

1. In Infisical, navigate to **Admin** → **Machine Identities**
2. Click **Create Machine Identity**
3. Enter a name: `terraform-cloud`
4. Optionally add a description: `OIDC authentication for Terraform Cloud`
5. Click **Create**

Note the **Machine Identity ID** (you'll need this later). It will look like: `machine-identity-abc123xyz789`

## Step 2: Add OIDC Auth Method

1. In the Machine Identity detail page, navigate to **Auth Methods**
2. Click **Add Auth Method** → **OIDC**
3. Configure the OIDC settings:

   | Field | Value |
   |-------|-------|
   | **OIDC Discovery URL** | `https://app.terraform.io` |
   | **Client ID** | `terraform` (or custom OIDC app ID from TFC) |
   | **Issuer** | `https://app.terraform.io` |
   | **Audience** | Match the value of `TFC_WORKLOAD_IDENTITY_AUDIENCE` in your TFC workspace (see Step 3) |

4. Click **Save**

### OIDC Discovery URL & Issuer Explanation

Terraform Cloud publishes its OIDC configuration at `https://app.terraform.io/.well-known/openid-configuration`. Both the discovery URL and issuer are the same for TFC: `https://app.terraform.io`.

## Step 3: Configure Terraform Cloud Workspace Variables

In your Terraform Cloud workspace:

1. Navigate to **Variables** (in the workspace settings)
2. Add **Environment Variable**: `TFC_WORKLOAD_IDENTITY_AUDIENCE`
   - Value: `aws.terraform.io` (or your custom audience identifier)
   - This must match the **Audience** configured in Step 2

3. Optionally add the Machine Identity ID as a variable for reference:
   - Name: `INFISICAL_MACHINE_IDENTITY_ID`
   - Value: `machine-identity-abc123xyz789` (from Step 1)
   - Mark as **Sensitive** if desired

Example TFC workspace variables:
```
TFC_WORKLOAD_IDENTITY_AUDIENCE=aws.terraform.io
INFISICAL_MACHINE_IDENTITY_ID=machine-identity-abc123xyz789
```

## Step 4: Configure the Infisical Provider in Terraform

Write the Infisical provider configuration in your Terraform code. The `TFC_WORKLOAD_IDENTITY_TOKEN` environment variable is automatically injected by Terraform Cloud during each run.

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "my-workspace"
    }
  }

  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.13"
    }
  }
}

variable "infisical_machine_identity_id" {
  type        = string
  description = "Machine Identity ID for OIDC authentication"
  sensitive   = true
}

provider "infisical" {
  identity_id                   = var.infisical_machine_identity_id
  token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
}
```

### Breakdown

- `identity_id`: The Machine Identity ID from Infisical (passed as a TFC variable)
- `token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"`: Tells the provider to read the OIDC token from this environment variable, which Terraform Cloud automatically sets

## Step 5: Grant Permissions to the Machine Identity

The Machine Identity needs permissions to access the secrets, projects, and environments it will interact with.

1. In Infisical, navigate to **Projects**
2. Select the project where your secrets live
3. Go to **Access Control** → **Machine Identities**
4. Assign the `terraform-cloud` Machine Identity with appropriate roles or permissions

Common permissions for Terraform:
- **Read secrets**: Allow the identity to fetch secrets via ephemeral resources
- **Manage resources** (if creating/updating project roles, policies, etc.): Grant higher-level permissions as needed

## Complete Working Example

```hcl
# versions.tf
terraform {
  cloud {
    organization = "my-company"
    workspaces {
      name = "production-secrets"
    }
  }

  required_version = ">= 1.10"
  required_providers {
    infisical = {
      source  = "infisical/infisical"
      version = "~> 0.13"
    }
  }
}

# variables.tf
variable "infisical_machine_identity_id" {
  type        = string
  description = "Infisical Machine Identity ID for OIDC"
  sensitive   = true
}

variable "infisical_workspace_id" {
  type        = string
  description = "Infisical workspace ID"
}

# main.tf
provider "infisical" {
  identity_id                   = var.infisical_machine_identity_id
  token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"
}

# Fetch secrets without storing them in state
ephemeral "infisical_secret" "db_password" {
  workspace_id = var.infisical_workspace_id
  env_slug     = "prod"
  secret_key   = "DATABASE_PASSWORD"
}

ephemeral "infisical_secret" "api_key" {
  workspace_id = var.infisical_workspace_id
  env_slug     = "prod"
  secret_key   = "API_KEY"
}

# Use secrets in resource configuration
resource "aws_db_instance" "main" {
  allocated_storage = 100
  engine            = "postgres"
  engine_version    = "15.2"
  instance_class    = "db.t3.micro"
  username          = "admin"
  password          = ephemeral.infisical_secret.db_password.value
  skip_final_snapshot = true
}

# outputs.tf
output "api_key" {
  value     = ephemeral.infisical_secret.api_key.value
  sensitive = true
}
```

**TFC Workspace Variables** (in Terraform Cloud):
```
TFC_WORKLOAD_IDENTITY_AUDIENCE = aws.terraform.io
INFISICAL_MACHINE_IDENTITY_ID = machine-identity-abc123xyz789
infisical_workspace_id = ws-prod-abc123
```

## Troubleshooting

### Error: "Invalid audience for OIDC token"

**Cause**: The `TFC_WORKLOAD_IDENTITY_AUDIENCE` variable in your TFC workspace doesn't match the **Audience** configured in the Infisical OIDC auth method.

**Solution**: Ensure both values are identical. For example, if you set `TFC_WORKLOAD_IDENTITY_AUDIENCE=aws.terraform.io`, the Infisical OIDC audience must also be `aws.terraform.io`.

### Error: "Identity not found" or "Unauthorized"

**Cause**: The Machine Identity ID is incorrect or the identity hasn't been granted permissions in the target project.

**Solution**:
1. Verify the Machine Identity ID matches what's in Infisical
2. Check that the identity has been assigned to the project with appropriate roles

### Error: "Token has expired" or "Invalid token"

**Cause**: The OIDC token is missing or invalid.

**Solution**:
1. Confirm `TFC_WORKLOAD_IDENTITY_TOKEN` is automatically set in your TFC workspace
2. Ensure `token_environment_variable_name = "TFC_WORKLOAD_IDENTITY_TOKEN"` is correct in your provider block
3. Re-run the plan to generate a fresh token

## Alternative CI/CD Platforms

### CircleCI OIDC

CircleCI also supports OIDC token generation. Configure it similarly:

1. Set up OIDC auth in Infisical with:
   - **Discovery URL**: `https://oidc.circleci.com/`
   - **Issuer**: `https://oidc.circleci.com/`
   - **Audience**: `https://circleci.com/` (or custom value)

2. In CircleCI, use the `CIRCLE_OIDC_TOKEN` environment variable:

```hcl
provider "infisical" {
  identity_id                   = var.infisical_machine_identity_id
  token_environment_variable_name = "CIRCLE_OIDC_TOKEN"
}
```

3. Configure CircleCI environment variables in your job context to pass the Machine Identity ID.

## Best Practices

1. **Rotate audiences**: Use unique audiences per TFC organization or workspace to improve audit trail clarity
2. **Minimal permissions**: Grant Machine Identities only the permissions they need (principle of least privilege)
3. **Audit logs**: Monitor Infisical audit logs for OIDC token exchanges to detect unauthorized access
4. **Environment-specific identities**: Create separate Machine Identities for dev, staging, and prod (don't share)
5. **Ephemeral resources**: Always use `ephemeral` resources to fetch secrets; never use data sources in production
