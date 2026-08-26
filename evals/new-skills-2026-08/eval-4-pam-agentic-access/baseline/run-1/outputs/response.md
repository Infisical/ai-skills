I don't have web or filesystem access in this session (no browsing tool, and I can't read your local `credential-brokering-101` scripts either), so I can't verify the exact current CLI flags against Infisical's live docs. Here's the architecture and command as I understand PAM today. Please confirm flag names with `infisical pam --help` before running this against prod, since PAM is a newer surface and syntax may have shifted since my training.

**The command**

```bash
# 1. One-time: an admin registers the DB in Infisical, giving it the real
#    admin/service credentials. These are encrypted at rest and never
#    handed back out in plaintext to any client.
infisical pam resource create postgres \
  --name prod-orders-db \
  --gateway-id <gateway-id>

# 2. Claude Code (or you, on its behalf) requests a time-boxed session
#    against that resource instead of asking for a connection string.
infisical pam connect prod-orders-db --ttl 30m
```

That second command opens a local ephemeral listener (e.g. `127.0.0.1:54329`) and hands Claude Code *that* address, not a real connection string. Anything talking to it (psql, an MCP query tool, an ORM) points at localhost.

**Where the real credential actually lives**

- The production DB password is stored encrypted in Infisical's backend and is only ever decrypted inside the **Gateway**, a small relay process you run inside your own VPC/network, next to the database.
- When Claude Code opens a connection to the local proxy port, that traffic is tunneled (mTLS) to the Gateway. The Gateway is the thing that authenticates to Postgres with the real password, at the protocol level, session by session.
- The agent's process never has the password in an env var, a file, its argv, or its context window. If a prompt injection or a bug made Claude Code try to print its "connection string," there is no secret in it to leak, just a loopback address that's meaningless outside that one TTL-bound session.
- The session is logged and expires automatically (your `--ttl`), so even a fully compromised agent only gets a bounded, audited window rather than a standing credential.

If you want Claude Code to never even see a connection string (not even the harmless local one), the tighter setup is to put PAM behind an MCP tool (e.g. a "query production DB" tool) so Claude Code passes SQL text in and rows come back. The credential brokering happens entirely server-side and the agent's tool call surface has no connection string at all. Happy to help wire that up if that's the direction you want, just confirm which pattern you're going for.
