Grant `describeSecret`, withhold `readValue`.

- **Grant**: `describeSecret` — lets developers see that a secret exists in production, including its metadata (name, tags, etc.)
- **Withhold**: `readValue` — this is what actually reveals the secret's value
- **Avoid**: `read` — this is the legacy action and grants both `describeSecret` and `readValue` together, so using it here would defeat the purpose

Scope this as a custom project role (or additional privilege) on the `secrets` subject for the production environment, with `describeSecret` allowed and `readValue` not included. Don't reach for the `viewer` built-in role either — it doesn't make this describe/read distinction.
