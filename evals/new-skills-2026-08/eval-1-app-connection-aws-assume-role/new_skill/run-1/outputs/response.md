Here's the exact request per the skill's AWS reference.

**Method:** `assume-role` (preferred over `access-key` — no static credentials stored)

```bash
curl -X POST 'https://us.infisical.com/api/v1/app-connections/aws' \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prod-aws",
    "method": "assume-role",
    "description": "Used by secrets-manager syncs in prod",
    "credentials": {
      "roleArn": "arn:aws:iam::123456789012:role/InfisicalAccess"
    }
  }'
```

**Credential fields for `assume-role`:**

| Field | Required | Notes |
|---|---|---|
| `roleArn` | Yes | The IAM role Infisical assumes |
| `stsEndpoint` | No | Must be HTTPS and an AWS-owned domain (`.amazonaws.com` / `.amazonaws.com.cn`) — for GovCloud, China regions, or PrivateLink STS, not a proxy |

One thing to set up on the AWS side before this works: the role's trust policy must trust Infisical's principal **and** require the External ID shown in the Infisical UI during setup. Skipping the External ID condition leaves the trust policy open to a confused-deputy attack.

The response returns a UUID `id` — that's the `connectionId` you'd pass into a Secret Sync, Secret Rotation, etc.

For scoping: grant only what the consuming feature needs (e.g. `secretsmanager:*` create/update/delete/list/describe plus KMS if using a CMK for a Secrets Manager sync; `ssm:PutParameter`/`GetParameter(s)`/`DeleteParameter`/`DescribeParameters` plus KMS for a Parameter Store sync).
