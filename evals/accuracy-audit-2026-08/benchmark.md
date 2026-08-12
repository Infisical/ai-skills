# Skill Accuracy Audit — Regression Eval
Iteration: `accuracy-audit-2026-08`  
Ground truth: `Infisical/infisical@caa698e100`  
Model: `claude-sonnet-5`, tools **disabled** on all arms  
Grading: deterministic regex (patterns in `eval_spec.json`)

## Why three arms
The usual skill-vs-no-skill A/B answers "does the skill help?". This audit needed a different question: **did the stale skills make things worse, and do the corrections fix that?** So each prompt runs against three contexts:

| Arm | Context |
|---|---|
| `baseline` | No skill |
| `old_skill` | Old skill (main) |
| `new_skill` | New skill (this branch) |

Tools are disabled so the model cannot look up the answer. That isolates what the skill text itself teaches.

## Results

| Arm | Score | Pass rate |
|---|---|---|
| No skill | 18/35 | **51.4%** |
| Old skill (main) | 13/35 | **37.1%** |
| New skill (this branch) | 35/35 | **100.0%** |

**The old skills scored below the no-skill baseline (37.1% vs 51.4%).** Stale content did not merely fail to help; it overrode correct model knowledge with wrong specifics. The corrected skills score 100.0%.

## Per-eval breakdown

| # | Eval | Skill | No skill | Old skill | New skill |
|---|---|---|---|---|---|
| 0 | `terraform-provider-auth-and-ephemeral` | infisical-terraform | 0/4 | 2/4 | 4/4 |
| 1 | `ruby-sdk-fetch-secret` | infisical-setup | 1/5 | 1/5 | 5/5 |
| 2 | `api-list-all-secrets` | infisical-api | 3/5 | 2/5 | 5/5 |
| 3 | `secret-sync-github-env-and-vercel` | infisical-secret-syncs | 5/5 | 2/5 | 5/5 |
| 4 | `agent-ssh-dynamic-secret-template` | infisical-agent | 2/4 | 2/4 | 4/4 |
| 5 | `self-host-fips-deployment` | infisical-self-host | 3/4 | 2/4 | 4/4 |
| 6 | `alicloud-machine-identity-auth` | infisical-setup | 2/4 | 0/4 | 4/4 |
| 7 | `dynamic-secrets-elasticache-tailscale` | infisical-dynamic-secrets | 2/4 | 2/4 | 4/4 |

## Notable cases

**eval-0 (Terraform)** — baseline 0/4, old skill 2/4, new skill 4/4. The old skill produced HCL that fails at plan time: credentials placed directly on the provider block instead of inside `auth = { universal = {...} }`, and `secret_key` instead of `name` on the ephemeral resource.

**eval-3 (Secret syncs)** — baseline **5/5**, old skill **2/5**, new skill 5/5. The clearest demonstration of harm: the base model already knew this correctly, and the old skill's invented enum values (`import-prioritize-vercel`, long-form GitHub visibility strings) actively degraded it.

**eval-6 (AliCloud auth)** — old skill **0/4**. The old skill documented 10 of the 13 auth methods, omitting AliCloud, OCI, and JWT entirely, so the model could not recommend the right one.

## Reproducing

```bash
python3 run_evals.py            # all evals, all arms
python3 run_evals.py 3          # single eval
python3 run_evals.py --regrade  # re-grade saved responses, no model calls
```

`old_skill` is read via `git show main:<path>`, so the comparison stays reproducible as long as the pre-audit state is reachable on `main`.

## Limitations

- Single run per cell; no variance estimate across repeated sampling.
- Deterministic regex grading checks that the right literals appear. It verifies correct identifiers, not that a whole config would deploy end to end.
- Assertions target the specific corrections this audit made. This is a regression suite, not a general measure of skill quality.
- eval-5's prompt was amended mid-run to ask which FIPS standard applies; the original wording never elicited a version number, so the assertion could not be judged. All three arms were re-run after the change.
