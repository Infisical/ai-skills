Here's the request to create an AWS App Connection using role assumption (not static access keys).

## 1. IAM side (prerequisite)

Create an IAM role in the target AWS account with a trust policy that lets Infisical's AWS account assume it, scoped with an external ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::<infisical-aws-account-id>:root" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "sts:ExternalId": "<your-infisical-org-id>" }
      }
    }
  ]
}
```

## 2. Create the App Connection

```
POST /api/v1/app-connections/aws
Host: app.infisical.com   (or your self-hosted instance)
Authorization: Bearer <access-token>
Content-Type: application/json
```

Body:

```json
{
  "name": "aws-prod",
  "description": "AWS connection via role assumption",
  "method": "assume-role",
  "credentials": {
    "roleArn": "arn:aws:iam::123456789012:role/InfisicalAssumeRole"
  }
}
```

cURL equivalent:

```bash
curl -X POST https://app.infisical.com/api/v1/app-connections/aws \
  -H "Authorization: Bearer $INFISICAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aws-prod",
    "description": "AWS connection via role assumption",
    "method": "assume-role",
    "credentials": {
      "roleArn": "arn:aws:iam::123456789012:role/InfisicalAssumeRole"
    }
  }'
```

Key points:
- `method` is `"assume-role"` (the alternative is `"access-key"`, which takes `credentials.accessKeyId` / `credentials.secretAccessKey` instead — that's the static-keys path you're avoiding).
- The only credential field for assume-role is `roleArn`. There's no secret material in the request body, since Infisical calls `sts:AssumeRole` at runtime using its own AWS identity and your trust policy's `ExternalId`.

One caveat: this session has no live network or filesystem access, so I built this from my trained knowledge of Infisical's App Connections implementation rather than pulling the current OpenAPI spec. Field names (`roleArn`, `method`) have been stable in this feature, but since you're at Infisical, it's worth a quick diff against `/api/docs` or the `app-connection/aws` service in the backend repo before shipping this against production.
