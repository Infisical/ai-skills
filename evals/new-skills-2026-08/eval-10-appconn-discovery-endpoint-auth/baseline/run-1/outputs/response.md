Two API calls do this: authenticate the machine identity to get an access token, then hit the App Connections endpoint that lists KMS keys reachable through your AWS connection (the same endpoint the Infisical UI uses to populate that dropdown when you configure a secret sync's KMS key field).

```python
import os
import requests

INFISICAL_API_URL = os.environ.get("INFISICAL_API_URL", "https://app.infisical.com")
CLIENT_ID = os.environ["INFISICAL_CLIENT_ID"]
CLIENT_SECRET = os.environ["INFISICAL_CLIENT_SECRET"]
AWS_APP_CONNECTION_ID = os.environ["AWS_APP_CONNECTION_ID"]  # UUID of the App Connection


def get_access_token() -> str:
    resp = requests.post(
        f"{INFISICAL_API_URL}/api/v1/auth/universal-auth/login",
        json={"clientId": CLIENT_ID, "clientSecret": CLIENT_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["accessToken"]


def list_kms_keys(access_token: str) -> list[dict]:
    resp = requests.get(
        f"{INFISICAL_API_URL}/api/v1/app-connections/aws/{AWS_APP_CONNECTION_ID}/kms-keys",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["kmsKeys"]  # each item: {id, alias, ...}


def main():
    token = get_access_token()
    keys = list_kms_keys(token)
    for k in keys:
        print(f"{k.get('alias') or '(no alias)'}  {k['id']}")

    chosen = next(k for k in keys if k.get("alias") == "alias/my-app-secrets")

    sync_config_payload = {
        "name": "my-secrets-sync",
        "connectionId": AWS_APP_CONNECTION_ID,
        "environment": "prod",
        "secretPath": "/",
        "destinationConfig": {
            "region": "us-east-1",
            "kmsKeyId": chosen["id"],
        },
    }
    # POST sync_config_payload to /api/v2/secret-syncs/aws-secrets-manager (or the sync
    # app you're targeting) once the KMS key is resolved.


if __name__ == "__main__":
    main()
```

Notes:

- Universal Auth (clientId/clientSecret) is the standard machine identity method for scripts. If this runs on an EC2 instance, Lambda, or ECS task, consider Infisical's AWS Auth method instead so the identity authenticates via the IAM role rather than a static secret.
- The machine identity needs permission to read App Connections (and to use/connect through that specific AWS connection), plus permission to create secret syncs in the target project.
- The exact field names in the KMS key list response (`id`, `alias`) and the destination config shape for the sync you're targeting (Secrets Manager vs. Parameter Store, etc.) can shift between Infisical versions. Since I can't hit their live API reference from this session, print the raw response once and confirm field names against your Infisical instance's API docs before wiring it into automation.

Separately: I don't have file or web access in this session (no Read/Write/Bash/WebFetch tools loaded), so I wrote this from what I know of Infisical's API rather than pulling it from your repo or verifying it live. If you want it checked against your actual `credential-brokering-101` scripts or the current API reference, that'll need to happen in a session where those tools are available.
