# Eval Results

Every Infisical AI Skill is A/B tested before shipping. Each eval runs the same prompt with and without the skill loaded, then grades the response against Infisical-specific assertions (correct function signatures, right auth method recommendations, accurate provider quirks, etc.).

## Summary

| Skill | With Skill | Without Skill | Delta | Directory |
|-------|-----------|--------------|-------|-----------|
| infisical-setup (v1) | 100% | 50% | **+50pp** | `infisical-setup-v1/` |
| infisical-setup (v2) | 100% | 50% | **+50pp** | `infisical-setup-v2/` |
| infisical-secret-syncs | 100% | 39% | **+61pp** | `infisical-secret-syncs/` |
| infisical-dynamic-secrets | 94% | 67% | **+28pp** | `infisical-dynamic-secrets/` |
| infisical-agent | 100% | 33% | **+67pp** | `infisical-agent/` |

**Overall Tier 1 accuracy: 98% with skills vs 46% without (+52pp)**

## Accuracy audit (`accuracy-audit-2026-08/`)

A separate three-arm regression eval run when the skills were re-verified against the
Infisical codebase. It answers a different question from the tables above — not "does a skill
help?" but **"has a skill gone stale, and did the corrections fix it?"**

| Arm | Score | Pass rate |
|-----|-------|-----------|
| No skill | 18/35 | 51.4% |
| Old skill (pre-audit) | 13/35 | **37.1%** |
| New skill (post-audit) | 35/35 | **100.0%** |

The important number is the middle one. **Stale skills scored below the no-skill baseline** —
outdated specifics didn't just fail to help, they overrode correct model knowledge. In the
secret-syncs case the base model scored 5/5 on its own and the stale skill dragged it to 2/5.

Tools are disabled on all arms in that suite, so the model cannot look up the answer and the
eval measures what the skill text itself teaches. Grading is deterministic regex rather than an
LLM judge. See [`accuracy-audit-2026-08/benchmark.md`](accuracy-audit-2026-08/benchmark.md).

**Takeaway for maintainers:** a skill that has drifted is worse than no skill at all. Re-verify
against the codebase whenever upstream adds providers, auth methods, or API versions.

## Structure

Each eval directory follows this layout:

```
<skill-name>/
├── iteration-1/
│   ├── benchmark.json       # Machine-readable aggregate results
│   ├── benchmark.md         # Human-readable summary
│   ├── eval-viewer.html     # Interactive HTML viewer (open in browser)
│   └── eval-N/
│       ├── eval_metadata.json   # Prompt + assertions for this test case
│       ├── with_skill/
│       │   └── run-1/
│       │       ├── grading.json     # Pass/fail per assertion with evidence
│       │       ├── timing.json      # Token count and duration
│       │       └── outputs/
│       │           └── response.md  # Full model response
│       └── without_skill/
│           └── run-1/
│               └── ...              # Same structure
```

## Viewing results

The easiest way to review results is to open the `eval-viewer.html` file in each skill's iteration directory. It shows side-by-side with/without responses and per-assertion grading.

## Methodology

Assertions test for Infisical-specific knowledge that AI agents commonly hallucinate, such as:

- Correct SDK package names and import paths
- Deprecated vs current auth patterns
- Provider-specific quirks (Azure underscore-to-hyphen conversion, GitHub no-import limitation)
- Exact function signatures and return types
- Required prerequisites (App Connections, admin users, IAM policies)
