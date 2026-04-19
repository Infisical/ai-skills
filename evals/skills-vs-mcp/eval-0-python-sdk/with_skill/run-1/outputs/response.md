# Infisical Python SDK for Flask Web Apps

This guide shows you how to integrate the Infisical Python SDK into your Flask application to securely fetch secrets at runtime from your Infisical instance.

## Installation

First, install the Infisical SDK using pip:

```bash
pip install infisicalsdk
```

**Requirements:** Python 3.7+ is required.

## Basic Setup in Flask

Here's a complete example of initializing the SDK, authenticating, and fetching secrets in your Flask app:

```python
from flask import Flask
from infisical_sdk import InfisicalSDKClient

app = Flask(__name__)

# Initialize the Infisical client
# Set cache_ttl to cache secrets in-memory (in seconds)
# Set to None if you want to disable caching
infisical_client = InfisicalSDKClient(
    host="https://app.infisical.com",  # or your self-hosted Infisical instance
    cache_ttl=300  # Cache secrets for 5 minutes
)

# Authenticate using Universal Auth (machine identity)
infisical_client.auth.universal_auth.login(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

@app.route("/")
def hello():
    # Fetch a single secret
    secret = infisical_client.secrets.get_secret(
        secret_name="API_KEY",
        project_id="YOUR_PROJECT_ID",
        environment_slug="dev"
    )
    api_key = secret.secret_value
    return f"Secret fetched: {api_key[:10]}..."

if __name__ == "__main__":
    app.run()
```

## Fetching All Secrets at Once

To fetch all secrets for your dev environment:

```python
# List all secrets in the dev environment
secrets = infisical_client.secrets.list_secrets(
    project_id="YOUR_PROJECT_ID",
    environment_slug="dev",
    secret_path="/"  # Root path to get all secrets
)

# Iterate through the secrets
for secret in secrets:
    print(f"Secret: {secret.secret_name} = {secret.secret_value}")
```

## Production-Ready Pattern

For a production Flask app, you'll want to initialize the client once at startup and reuse it. Here's a recommended approach:

```python
from flask import Flask
from infisical_sdk import InfisicalSDKClient
import os

app = Flask(__name__)

class Config:
    """Configuration loaded from Infisical"""
    def __init__(self):
        self.client = InfisicalSDKClient(
            host=os.getenv("INFISICAL_HOST", "https://app.infisical.com"),
            cache_ttl=300  # Cache for 5 minutes
        )
        
        # Authenticate once at startup
        self.client.auth.universal_auth.login(
            client_id=os.getenv("INFISICAL_CLIENT_ID"),
            client_secret=os.getenv("INFISICAL_CLIENT_SECRET")
        )
        
        # Load all secrets for your environment
        self._load_secrets()
    
    def _load_secrets(self):
        """Load all secrets from Infisical at startup"""
        secrets = self.client.secrets.list_secrets(
            project_id=os.getenv("INFISICAL_PROJECT_ID"),
            environment_slug=os.getenv("ENVIRONMENT", "dev"),
            secret_path="/"
        )
        
        # Convert to a dictionary for easy access
        self.secrets = {secret.secret_name: secret.secret_value for secret in secrets}
    
    def get_secret(self, secret_name):
        """Get a secret by name"""
        return self.secrets.get(secret_name)

# Initialize config at startup
config = Config()
app.config.update(config.secrets)

@app.route("/test-secret")
def test_secret():
    api_key = config.get_secret("API_KEY")
    return {"success": api_key is not None}

if __name__ == "__main__":
    app.run()
```

## Authentication Methods

The Infisical Python SDK supports multiple authentication methods. **Universal Auth** (shown above) is recommended for most machine-to-machine scenarios. Other available methods include:

- **AWS IAM Auth** — Recommended if your Flask app runs on AWS (EC2, Lambda, etc.)
- **Kubernetes Auth** — Recommended if deploying to Kubernetes
- **OIDC** — For OpenID Connect providers
- **LDAP** — For LDAP-based authentication
- **Token Auth** — Basic token-based authentication

Example with AWS IAM Auth:

```python
infisical_client.auth.aws_iam_auth.login(
    identity_id="YOUR_IDENTITY_ID"
)
```

## Best Practices

1. **Use environment variables for credentials** — Never hardcode your `client_id` and `client_secret`:
   ```python
   client_id = os.getenv("INFISICAL_CLIENT_ID")
   client_secret = os.getenv("INFISICAL_CLIENT_SECRET")
   ```

2. **Leverage caching** — Set `cache_ttl` to avoid excessive API calls:
   ```python
   infisical_client = InfisicalSDKClient(host="...", cache_ttl=300)
   ```

3. **Consider zero-secret authentication** — If on AWS or Kubernetes, use the native auth methods (AWS IAM or Kubernetes Auth) to avoid managing credentials altogether.

4. **Avoid deprecated patterns** — **Do not use** Service Tokens (prefixed with `st.`) or API Keys. These are deprecated. Always use machine identities instead.

5. **Handle errors gracefully**:
   ```python
   try:
       secret = infisical_client.secrets.get_secret(...)
   except Exception as e:
       app.logger.error(f"Failed to fetch secret: {e}")
       # Fallback behavior or exit gracefully
   ```

## Troubleshooting

- **Authentication fails** — Verify your `client_id` and `client_secret` are correct and have the right permissions in Infisical.
- **Secrets not found** — Confirm the `project_id`, `environment_slug`, and `secret_name` match exactly.
- **Performance concerns** — Increase `cache_ttl` to reduce API calls, or load secrets once at startup (see the production pattern above).

## Next Steps

- Review the [Infisical documentation](https://infisical.com/docs) for advanced features
- Set up environment-specific secret paths for staging/production
- Consider integrating secret rotation policies for sensitive credentials
