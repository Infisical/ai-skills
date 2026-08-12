# Routing Eval — Does the Right Skill Get Picked?

Iteration `routing-2026-08` · model `claude-sonnet-5` · tools **disabled**

## Why this eval exists

Going from 7 to 17 skills makes **mis-routing** the dominant failure mode. A skill that is never
loaded is useless; a skill loaded for the wrong question is worse, because it answers confidently
from the wrong frame.

Every case sits deliberately on a seam between two skills that sound alike. The measured question
is not "is the answer correct" but "was the correct skill selected".

| Arm | Context given |
|---|---|
| `descriptions` | Skill descriptions only |
| `router` | AGENTS.md router + boundaries |

## Results

| Arm | Correct | Accuracy |
|---|---|---|
| Skill descriptions only | 13/14 | **92.9%** |
| AGENTS.md router + boundaries | 14/14 | **100.0%** |

## Per-case

| # | Seam being tested | Expected | Descriptions only | With router |
|---|---|---|---|---|
| 0 | `rotation-not-dynamic` | infisical-secret-rotation | OK | OK |
| 1 | `dynamic-not-rotation` | infisical-dynamic-secrets | OK | OK |
| 2 | `pam-not-dynamic` | infisical-pam | OK | OK |
| 3 | `app-connection-not-machine-identity` | infisical-app-connections | OK | OK |
| 4 | `machine-identity-not-app-connection` | infisical-setup | OK | OK |
| 5 | `sso-not-machine-identity-oidc` | infisical-sso | OK | OK |
| 6 | `ssh-cert-not-pki` | infisical-dynamic-secrets | **infisical-pam** | OK |
| 7 | `operator-not-selfhost` | infisical-kubernetes-operator | OK | OK |
| 8 | `kms-not-secret-storage` | infisical-kms | OK | OK |
| 9 | `pki-sync-not-secret-sync` | infisical-pki | OK | OK |
| 10 | `gateway-not-selfhost` | infisical-gateway | OK | OK |
| 11 | `granular-secret-permission` | infisical-access-control | OK | OK |
| 12 | `agent-not-operator` | infisical-agent | OK | OK |
| 13 | `scanning-github-radar` | infisical-secret-scanning | OK | OK |

## Finding

The router closes the gap: **14/14** with it versus
**13/14** on descriptions alone.

The case it fixed was `ssh-cert-not-pki`. Asked about short-lived SSH certificates, descriptions
alone routed to `infisical-pam` — plausible, since PAM does broker SSH access, but wrong: SSH
certificates are issued by **SSH dynamic secrets**, not by the PKI product and not by PAM. The
disambiguation table states that explicitly, and with it the routing is correct.

Descriptions alone already handle most seams, which is expected — the frontmatter descriptions were
written with boundaries in mind. The router earns its place on the residual cases where two skills
both genuinely touch the topic.

## Limitations

- Single run per cell.
- Measures skill *selection* given a well-formed question, not end-to-end answer quality.
- 14 hand-picked confusable pairs, not a representative sample of real user questions.
- `app-connection-not-machine-identity` was amended after the first run: the original prompt named a
  Secret Sync, which made `infisical-secret-syncs` a defensible answer and tested the wrong seam.
  Both arms were re-run after rewording. The original wording is recorded in `routing_spec.json`.
