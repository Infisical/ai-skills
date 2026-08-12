# Routing Eval — Does the Right Skill Get Picked?

Iteration `routing-2026-08` · model `claude-sonnet-5` · tools **disabled**

## Why this eval exists

Going from 7 to 17 skills makes **mis-routing** the dominant failure mode. A skill that is never
loaded is useless; a skill loaded for the wrong question is worse, because it answers confidently
from the wrong frame.

Every case sits deliberately on a seam between two skills that sound alike. The measured question is
not "is the answer correct" but "was the correct skill selected".

| Arm | Context given |
|---|---|
| `descriptions` | The 17 skill frontmatter `description` fields only |
| `router` | AGENTS.md router + disambiguation table, plus the descriptions |

**The `descriptions` arm is the one that matters.** In a real client the `description` frontmatter is
what decides whether a skill loads at all; AGENTS.md and the in-skill `## Not this skill` sections
only help once a skill is already in context.

## Results

| Arm | Correct | Accuracy |
|---|---|---|
| Skill descriptions only | 14/14 | **100.0%** |
| AGENTS.md router + boundaries | 14/14 | **100.0%** |

## What this measured, and what changed

Run 1 — boundaries lived only in AGENTS.md and in each skill's `## Not this skill` body:

| Arm | Result |
|---|---|
| Descriptions only | 13/14 |
| With router | 14/14 |

The router closed the gap, but that relied on AGENTS.md being in context. The failing case was
`ssh-cert-not-pki`: asked about short-lived SSH certificates, descriptions alone chose
`infisical-pam` — plausible, since PAM does broker SSH access, but wrong. SSH certificates are
issued by **SSH dynamic secrets**, not by PAM and not by the PKI product.

Run 2 — after adding a short negative-boundary clause to **all 17 `description` fields**
(e.g. dynamic-secrets now states it is "not for changing an existing credential on a schedule"):

| Arm | Result |
|---|---|
| Descriptions only | **14/14** |
| With router | 14/14 |

Routing is now correct from the descriptions alone, so it no longer depends on the router being
loaded. The router and the in-skill sections remain useful for the *answer* — they tell a
correctly-loaded skill where to hand off — but they are no longer load-bearing for *selection*.

## Per-case

| # | Seam tested | Expected | Descriptions | With router |
|---|---|---|---|---|
| 0 | `rotation-not-dynamic` | infisical-secret-rotation | OK | OK |
| 1 | `dynamic-not-rotation` | infisical-dynamic-secrets | OK | OK |
| 2 | `pam-not-dynamic` | infisical-pam | OK | OK |
| 3 | `app-connection-not-machine-identity` | infisical-app-connections | OK | OK |
| 4 | `machine-identity-not-app-connection` | infisical-setup | OK | OK |
| 5 | `sso-not-machine-identity-oidc` | infisical-sso | OK | OK |
| 6 | `ssh-cert-not-pki` | infisical-dynamic-secrets | OK | OK |
| 7 | `operator-not-selfhost` | infisical-kubernetes-operator | OK | OK |
| 8 | `kms-not-secret-storage` | infisical-kms | OK | OK |
| 9 | `pki-sync-not-secret-sync` | infisical-pki | OK | OK |
| 10 | `gateway-not-selfhost` | infisical-gateway | OK | OK |
| 11 | `granular-secret-permission` | infisical-access-control | OK | OK |
| 12 | `agent-not-operator` | infisical-agent | OK | OK |
| 13 | `scanning-github-radar` | infisical-secret-scanning | OK | OK |

## Limitations

- Single run per cell.
- Measures skill *selection* given a well-formed question, not end-to-end answer quality.
- 14 hand-picked confusable pairs, not a representative sample of real questions.
- Both arms present all 17 descriptions at once. A real client may score differently when matching
  a description against a conversation rather than choosing from a list.
- `app-connection-not-machine-identity` was amended after the first run: the original prompt named a
  Secret Sync, which made `infisical-secret-syncs` defensible and tested the wrong seam. Both arms
  were re-run after rewording; the note is preserved in `routing_spec.json`.
