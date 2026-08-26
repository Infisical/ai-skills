Quick flag before the how-to: the endpoint you're describing (`GET /api/v1/app-connections/aws/{connectionId}/kms-keys`) is one of the 88 JWT-only discovery endpoints. It's built for the Infisical UI dropdown, not automation, and it will reject a machine identity access token outright. No method or header workaround changes that.

Here's the correct path, per the skill's guidance (option 1: ask the provider directly, since Infisical isn't the system of record for AWS's own resources):

**1. Authenticate to Infisical as usual** (unrelated to KMS listing, but you'll need the token for the sync call later):

```bash
TOKEN=$(curl -s -X POST 'https://us.infisical.com/api/v1/auth/universal-auth/login' \
  -d "clientId=$CLIENT_ID&clientSecret=$CLIENT_SECRET" | jq -r .accessToken)
```

**2. Resolve your AWS App Connection's ID by name** (this one *does* accept a machine identity token):

```bash
CONN=$(curl -s 'https://us.infisical.com/api/v1/app-connections/aws/connection-name/prod-aws' \
  -H "Authorization: Bearer $TOKEN")
CONNECTION_ID=$(echo "$CONN" | jq -r .appConnection.id)
```

**3. List KMS keys via the AWS SDK directly**, using the same role/region the connection is configured with:

```python
import boto3

session = boto3.Session(region_name="us-east-1")  # or sts.assume_role with the connection's roleArn
kms = session.client("kms")

keys = []
paginator = kms.get_paginator("list_keys")
for page in paginator.paginate():
    for k in page["Keys"]:
        keys.append(k["KeyId"])
```

If your script doesn't already have AWS credentials locally, assume the same `roleArn` the App Connection uses (or a role with equivalent read access) with `sts.AssumeRole`, then build the `boto3.Session` from those temporary credentials.

**4. Fill in the secret sync's `destinationConfig`** with the key ID/ARN you got from AWS, referencing `CONNECTION_ID` from step 2:

```bash
curl -X POST 'https://us.infisical.com/api/v1/secret-syncs/aws-secrets-manager' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"prod-sync\",
    \"connectionId\": \"$CONNECTION_ID\",
    \"destinationConfig\": { \"region\": \"us-east-1\", \"kmsKeyId\": \"$KEY_ID\" }
  }"
```

The two other fallback options if you'd rather not touch the AWS SDK: read the key ID once out of the Infisical UI and hardcode it, or create the sync once in the UI and `GET` it back through the API to copy the exact `destinationConfig` shape it produced.
