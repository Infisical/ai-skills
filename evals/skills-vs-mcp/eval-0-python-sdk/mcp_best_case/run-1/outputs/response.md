# Infisical Python SDK Setup for Flask

This guide shows you how to integrate Infisical's Python SDK into your Flask web app to fetch secrets at runtime using Universal Auth.

## Step 1: Install the SDK

```bash
pip install infisicalsdk
```

Requires Python 3.7+.

## Step 2: Initialize and Authenticate

Here's a minimal Flask app that initializes the Infisical client and authenticates using machine identity credentials:

```python
from flask import Flask
from infisical_sdk import InfisicalSDKClient

app = Flask(__name__)

# Initialize the Infisical client
# For self-hosted instances, replace host with your URL
client = InfisicalSDKClient(host="https://app.infisical.com")

# Authenticate using Universal Auth with machine identity credentials
client.auth.universal_auth.login(
    client_id="<your-machine-identity-client-id>", 
    client_secret="<your-machine-identity-client-secret>"
)
```

**Note:** Replace `<your-machine-identity-client-id>` and `<your-machine-identity-client-secret>` with your actual machine identity credentials created in Infisical.

## Step 3: Fetch All Secrets for Dev Environment

To fetch all secrets from your dev environment, use the `list_secrets` method:

```python
# Fetch all secrets from your project's dev environment
secrets = client.secrets.list_secrets(
    project_id="<your-project-id>",
    environment_slug="dev",
    secret_path="/"
)

# Iterate through and use secrets
for secret in secrets:
    print(f"{secret.secret_key}: {secret.secret_value}")
```

Replace `<your-project-id>` with your actual Infisical project ID.

## Complete Flask Example

Here's a more realistic setup that initializes the client once at app startup:

```python
from flask import Flask
from infisical_sdk import InfisicalSDKClient
import os

app = Flask(__name__)

# Initialize client once at startup
infisical_client = InfisicalSDKClient(
    host="https://app.infisical.com"  # or your self-hosted URL
)

# Authenticate using credentials from environment variables
infisical_client.auth.universal_auth.login(
    client_id=os.getenv("INFISICAL_CLIENT_ID"),
    client_secret=os.getenv("INFISICAL_CLIENT_SECRET")
)

# Fetch secrets once and cache them
app.config['SECRETS'] = infisical_client.secrets.list_secrets(
    project_id=os.getenv("INFISICAL_PROJECT_ID"),
    environment_slug="dev",
    secret_path="/"
)

@app.route('/')
def index():
    return "Flask app with Infisical secrets loaded!"

if __name__ == "__main__":
    app.run(debug=False)
```

## Client Configuration Options

The `InfisicalSDKClient` accepts the following parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `host` | str (optional) | The Infisical instance URL. Defaults to `https://app.infisical.com`. Use for self-hosted instances. |
| `token` | str (optional) | Direct authentication token. Use as an alternative to `auth.universal_auth.login()`. |
| `cache_ttl` | int (optional) | Secret cache TTL in seconds (default: 60). Set to `None` to disable caching. |

## Alternative: Direct Token Authentication

If you already have an authentication token, you can skip the `login()` call:

```python
client = InfisicalSDKClient(
    host="https://app.infisical.com",
    token="<your-auth-token>"
)
```

## Other Available Methods

Beyond `list_secrets()`, the SDK provides:
- `create_secret_by_name()` — Create a new secret
- `get_secret_by_name()` — Fetch a single secret by name
- `update_secret_by_name()` — Update an existing secret
- `delete_secret_by_name()` — Delete a secret

Example:
```python
# Fetch a single secret
db_password = client.secrets.get_secret_by_name(
    secret_name="DB_PASSWORD",
    project_id="<your-project-id>",
    environment_slug="dev"
)
```

## Best Practices

1. **Store credentials securely** — Use environment variables for `client_id` and `client_secret`, never hardcode them.
2. **Use caching** — The default 60-second TTL (`cache_ttl=60`) reduces API calls. Adjust as needed for your app.
3. **Handle authentication errors** — Wrap login calls in try-except to handle credential issues gracefully.
4. **Load secrets at startup** — Initialize the client and fetch secrets once when the Flask app starts, not on every request.

## Self-Hosted Infisical

If you're running a self-hosted instance, change the `host` parameter:

```python
client = InfisicalSDKClient(host="https://infisical.yourdomain.com")
```

That's it! Your Flask app can now securely fetch secrets from Infisical at runtime.
