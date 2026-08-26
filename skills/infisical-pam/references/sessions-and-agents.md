# PAM Sessions and Agentic Access

## Session lifecycle

`PamSessionStatus`:

| Status | Meaning |
|--------|---------|
| `starting` | Session is being established |
| `active` | Live and connected |
| `ended` | Finished normally |
| `terminated` | Killed by an admin |

`PamSessionEndReason`:

| Reason | Meaning |
|--------|---------|
| `completed` | The user disconnected |
| `expired` | Hit the template's maximum session duration |

Note `terminated` is a distinct status from `ended` — an admin killing a live session is
distinguishable in the audit trail from a user disconnecting. That distinction matters in an
incident review.

### The stages

1. **Requesting access** — if the account is gated, an approval must clear first
2. **Connecting** — role, duration, and approval are checked; the session opens
3. **During the session** — every query (database) or command (SSH) is captured
4. **Ending** — the user disconnects, the duration expires, or an admin terminates it
5. **After** — the recording and audit record remain for review

AI agents go through exactly the same stages, with the same checks and the same recording.

## Recording

- **Every query or command is captured** — SQL for databases, commands for SSH.
- **Recordings are available in real time.** You can review activity while the session is still active.
- **An admin can terminate a live session.**

Those two together are the incident-response story: you can watch what is happening and cut it off
mid-stream, rather than reading about it afterwards.

Admins and Auditors review sessions from the **Sessions** page.

Give Auditor to your security team rather than Admin. It grants exactly the review capability
without the ability to change accounts or memberships.

## Access methods

`PamAccessMethod` is `web` or `cli`.

| Method | Best for |
|--------|---------|
| `web` | Occasional human access, auditors, anyone without the CLI. Nothing to install |
| `cli` | Engineers who want their own tooling; the basis for agentic access |

## Agentic access for AI agents

The problem this solves: the usual way to give an AI agent database access is a connection string in
its environment — a long-lived credential sitting in a process that reads untrusted input all day.

Agentic access brokers it instead. **No credential ever reaches the agent.**

```bash
infisical pam agentic access -- claude
```

Everything after `--` is the command that starts your agent.

### How it works

Each account the agent may use is opened as a **port on `127.0.0.1`**. The agent connects to a local
port as it would to any database or host; the **Gateway on the far side injects the real
credential**.

```
Agent (sandboxed, no credentials)
  --> 127.0.0.1:52431
        --> Infisical CLI (one local port per account)
              --> encrypted tunnel --> Gateway (adds the real credential) --> target
```

Four properties worth stating explicitly:

1. **Ports open first and nothing is connected.** No session exists until the agent actually reaches for an account.
2. **The first connection opens the session**, subject to the usual checks: role, duration, and approval.
3. **The Gateway holds the credential** and injects it in transit. The agent authenticates to nothing and stores nothing.
4. **Everything is recorded**, attributed to whoever the run authenticated as — exactly like a person's session.

### Scoping which accounts

By default the agent can reach **every account you could launch a session on yourself**, which is
almost always more than a task needs. Narrow it:

```bash
infisical pam agentic access \
  --account prod/orders-db \
  --account prod/bastion \
  -- claude
```

Always recommend `--account`. Least privilege for agents is the same discipline as for people, and
the default here is deliberately broad.

### Who the agent runs as

An agent has **no access of its own** — it borrows the access of whoever starts the run:

| Runs as | When | Attribution |
|---------|------|-------------|
| **You** (`infisical login`) | Interactive work with a coding agent at your terminal | Sessions and access requests are attributed to you |
| **A machine identity** | Unattended runs, scheduled jobs | Sessions and requests belong to the identity |

For anything running with nobody watching, give it a machine identity of its own. Otherwise a
nightly job's activity appears in the audit trail under a person's name, which is misleading and
breaks when they leave.

### Prerequisites

- The **Infisical CLI**, with either `infisical login` completed or a machine identity to authenticate as
- **Connector or Admin role** on the folders or accounts the agent should reach, held by whoever the run authenticates as
- **macOS**, or **Linux with [bubblewrap](https://github.com/containers/bubblewrap)** installed

The sandbox comes from the operating system. Where one is unavailable the command **refuses to
start** unless you explicitly turn the sandbox off. Do not suggest disabling the sandbox as a
convenience — it is the boundary keeping the agent away from the rest of the machine.

### Agent support

Claude Code, Codex, and Gemini are recognized by name and are told what they can reach in their own
format. An agent you wrote yourself reads the same instructions from an environment variable, so any
agent can be run this way.

### Related CLI commands

| Command | Purpose |
|---------|---------|
| `infisical pam access` | Launch a session as a person |
| `infisical pam agentic access` | Launch an agent with brokered access |

## Auditing

Every session produces an audit record and a recording. Combined with a template that requires a
reason, you get: who connected, to what, when, for how long, why, and everything they did.

For streaming audit events to an external SIEM see `infisical-access-control`, which covers audit
log streams.

## Recommendations

- **Require a reason and MFA on production templates.** The reason field is what makes the record intelligible later.
- **Gate production accounts with access requests**, and leave dev ungated to avoid approval fatigue.
- **Grant Auditor to security**, Connector to engineers, Admin to as few people as possible.
- **Machine identity per unattended agent**, not a shared one, so you can revoke a single agent.
- **Always pass `--account`** when starting an agent.
- **Set the shortest workable maximum session duration.** Sessions expire with reason `expired`, which is a clean, auditable outcome.
