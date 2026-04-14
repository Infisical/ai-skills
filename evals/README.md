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
