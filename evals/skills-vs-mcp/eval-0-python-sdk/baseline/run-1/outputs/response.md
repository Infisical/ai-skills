# Fetching Secrets from Infisical in Flask Using the Python SDK

This guide walks through installing, initializing, and using the Infisical Python SDK to fetch secrets at runtime in a Flask web app.

## 1. Installation

Install the Infisical Python SDK via pip:

```bash
pip install infisical-python
```

Alternatively, if you're using a `requirements.txt`:

```
infisical-python>=0.1.0
```

Then run:

```bash
pip install -r requirements.txt
```

## 2. SDK Initialization & Authentication

The Python SDK supports multiple authentication methods. Here are the most common for a Flask app:

### Option A: Using Machine Identity (Recommended for Production)

Machine identities allow your Flask app to authenticate without storing passwords:

```python
from infisical import InfisicalClient
from infisical.models import GetSecretsRequestBody, AuthMethod

# Initialize the client
client = InfisicalClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    auth_method=AuthMethod.CLIENT_CREDENTIALS,
    host="https://your-infisical-instance.com"  # Omit for Infisical Cloud (default)
)

# Authenticate (credentials are exchanged for an access token)
client.auth()
```

### Option B: Using API Key (Simpler, suitable for development)

```python
from infisical import InfisicalClient

# Initialize with API key
client = InfisicalClient(
    api_key="your_api_key_here",
    host="https://your-infisical-instance.com"  # Omit for Infisical Cloud
)
```

### Option C: Using Universal Auth (Token-based)

```python
from infisical import InfisicalClient
from infisical.models import AuthMethod

client = InfisicalClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    auth_method=AuthMethod.UNIVERSAL_AUTH,
    host="https://your-infisical-instance.com"
)

client.auth()
```

## 3. Fetching Secrets

Once initialized and authenticated, fetch secrets using the client:

### Fetch a Single Secret

```python
from infisical.models import GetSecretRequestBody

secret = client.getSecret(
    options=GetSecretRequestBody(
        environment="dev",  # or "staging", "prod", etc.
        project_id="your_project_id",
        secret_name="DATABASE_PASSWORD"
    )
)

print(secret.secret_value)  # Access the secret value
```

### Fetch All Secrets for an Environment

```python
from infisical.models import GetSecretsRequestBody

secrets = client.getSecrets(
    options=GetSecretsRequestBody(
        environment="dev",
        project_id="your_project_id"
    )
)

# secrets is a list of Secret objects
for secret in secrets:
    print(f"{secret.key} = {secret.value}")
```

## 4. Complete Flask App Example

Here's a minimal Flask app that fetches secrets from Infisical at startup:

```python
from flask import Flask
from infisical import InfisicalClient
from infisical.models import GetSecretsRequestBody

# Initialize Flask app
app = Flask(__name__)

# Initialize Infisical client (use environment variables for credentials)
import os

client = InfisicalClient(
    client_id=os.getenv("INFISICAL_CLIENT_ID"),
    client_secret=os.getenv("INFISICAL_CLIENT_SECRET"),
    host=os.getenv("INFISICAL_HOST", "https://app.infisical.com")
)

# Authenticate
client.auth()

# Fetch all secrets for dev environment at startup
def load_secrets():
    try:
        secrets_list = client.getSecrets(
            options=GetSecretsRequestBody(
                environment="dev",
                project_id=os.getenv("INFISICAL_PROJECT_ID")
            )
        )
        
        # Convert to dictionary for easy access
        secrets_dict = {secret.key: secret.value for secret in secrets_list}
        return secrets_dict
    except Exception as e:
        print(f"Failed to load secrets: {e}")
        return {}

# Load secrets at startup
app.config.update(load_secrets())

@app.route('/')
def hello():
    # Access secrets via Flask config
    db_password = app.config.get('DATABASE_PASSWORD', 'default_value')
    return f"Hello! DB Password: {db_password}"

if __name__ == '__main__':
    app.run(debug=False)
```

## 5. Environment Setup

Create a `.env` file (or set these in your deployment environment):

```bash
INFISICAL_CLIENT_ID=your_client_id
INFISICAL_CLIENT_SECRET=your_client_secret
INFISICAL_PROJECT_ID=your_project_id
INFISICAL_HOST=https://your-infisical-instance.com  # Optional, defaults to Infisical Cloud
```

For development, use `python-dotenv` to load these:

```python
from dotenv import load_dotenv
import os

load_dotenv()

client = InfisicalClient(
    client_id=os.getenv("INFISICAL_CLIENT_ID"),
    client_secret=os.getenv("INFISICAL_CLIENT_SECRET")
)
```

Install `python-dotenv`:

```bash
pip install python-dotenv
```

## 6. Advanced: Caching & Refresh

For production, consider caching secrets to reduce API calls:

```python
from functools import lru_cache
import time

class SecretManager:
    def __init__(self, client, cache_ttl=300):
        self.client = client
        self.cache_ttl = cache_ttl
        self._cache = None
        self._cache_time = 0
    
    def get_secrets(self, environment, project_id):
        # Return cached secrets if still valid
        if self._cache and (time.time() - self._cache_time) < self.cache_ttl:
            return self._cache
        
        # Fetch fresh secrets
        secrets_list = self.client.getSecrets(
            options=GetSecretsRequestBody(
                environment=environment,
                project_id=project_id
            )
        )
        
        self._cache = {secret.key: secret.value for secret in secrets_list}
        self._cache_time = time.time()
        return self._cache

# Usage in Flask
secret_manager = SecretManager(client, cache_ttl=300)  # 5-minute cache
app.config.update(secret_manager.get_secrets("dev", os.getenv("INFISICAL_PROJECT_ID")))
```

## 7. Error Handling

Always wrap secret fetching in try-except blocks:

```python
from infisical.exceptions import InfisicalError

try:
    secrets = client.getSecrets(
        options=GetSecretsRequestBody(
            environment="dev",
            project_id="your_project_id"
        )
    )
except InfisicalError as e:
    print(f"Infisical API error: {e}")
    # Fall back to environment variables or raise
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
```

## Summary

1. **Install**: `pip install infisical-python`
2. **Authenticate**: Use client ID/secret (machine identity) or API key
3. **Fetch**: Call `client.getSecrets()` for all secrets or `client.getSecret()` for a single one
4. **Config**: Store credentials in environment variables, load at startup
5. **Cache**: Optionally cache secrets with a TTL to reduce API calls
6. **Error Handling**: Wrap calls in try-except for robustness

This approach ensures your Flask app can securely fetch and use secrets from Infisical at runtime.
