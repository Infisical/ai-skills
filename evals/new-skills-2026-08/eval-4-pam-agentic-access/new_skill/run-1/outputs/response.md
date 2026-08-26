The command:

```bash
infisical pam agentic access --account prod/orders-db -- claude
```

Replace `prod/orders-db` with your actual account path. Pass one `--account` flag per resource Claude Code should be able to reach, since by default it would get every account you personally have access to, which is broader than needed here.

**How the credential stays away from Claude**

1. `infisical pam agentic access` opens a local port on `127.0.0.1` for each account you passed. No session exists yet, nothing is connected.
2. Claude Code starts inside an OS-level sandbox (macOS, or Linux with bubblewrap) with only those local ports reachable.
3. When Claude actually queries the database, it connects to `127.0.0.1:<port>` like it would to any normal Postgres/MySQL/etc endpoint. That first connection is what opens the PAM session, and standard checks run (your role, template max duration, whether the account requires approval).
4. The local port hands off through an encrypted tunnel to the Gateway. The Gateway is the only thing that ever holds the real password. It injects the credential into the connection on the far side, so Claude never authenticates with anything real, never stores a secret, and never sees a connection string.
5. Every query gets recorded, attributed to whoever ran the command (you, if you're logged in via `infisical login`, or a machine identity if this runs unattended).

Prerequisites: the Infisical CLI authenticated (`infisical login` or a machine identity), and Connector or Admin role on that account, held by whoever the run authenticates as.

One thing to decide: if `prod/orders-db` is a gated account requiring approval, the first query will block until an approver signs off. If it's meant for unattended use, use a machine identity instead of your own login so the audit trail doesn't show your name for something running while you're not watching.
