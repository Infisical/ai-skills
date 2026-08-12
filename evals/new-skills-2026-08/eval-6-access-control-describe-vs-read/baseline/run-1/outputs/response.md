In Infisical's project role permissions, secrets have separate actions for metadata visibility versus decrypted value access. For this policy:

**Grant:**
- `describeSecret` — lets someone see that a secret key exists, along with its metadata (tags, comments, secret path, rotation/version info) without decrypting it.

**Withhold:**
- `readValue` — this is the action that actually decrypts and returns the secret's value. Leaving it unchecked means the UI/API will show the key exists but the value stays hidden (masked).

Both actions live under the `secrets` subject in the Project Role editor (Access Control → Project Roles → create/edit a role → Secrets permission row). To scope it to production only, add a condition on the policy: `Environment = production` (you can also add a secret path condition if you want to limit which paths this applies to, e.g. only certain folders).

A few things to decide separately, since you didn't mention them:
- `create` / `edit` / `delete` are independent actions — leave those unchecked too if developers should be strictly read-only in prod.
- If they need this same visibility in other environments (staging, dev), you'd need a second policy row or a broader condition, since the production restriction only applies to the specific condition you set.
- This describeSecret/readValue split is enforced per-role, so make sure developers aren't in another role (e.g. a default "Developer" role) that already grants `readValue` broadly, since Infisical grants the union of permissions across all assigned roles.

If you want, I can walk through the actual JSON policy shape used by the API/Terraform provider for scripting this instead of doing it through the UI.
