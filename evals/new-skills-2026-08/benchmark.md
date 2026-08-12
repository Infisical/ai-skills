# New Skills — A/B Eval

Iteration `new-skills-2026-08` · ground truth `Infisical/infisical@caa698e100` · model `claude-sonnet-5` · tools **disabled** · deterministic regex grading.

One eval per newly added skill, asserting facts verified against the codebase.

## Results

| Arm | Score | Pass rate |
|---|---|---|
| No skill | 21/46 | **45.6%** |
| With new skill | 46/46 | **100.0%** |

## Per-eval

| # | Eval | Skill | No skill | With skill |
|---|---|---|---|---|
| 0 | `rotation-sql-two-user` | infisical-secret-rotation | 3/5 | 5/5 |
| 1 | `app-connection-aws-assume-role` | infisical-app-connections | 4/4 | 4/4 |
| 2 | `pki-ecdsa-key-algorithm` | infisical-pki | 1/4 | 4/4 |
| 3 | `kms-sign-isdigest` | infisical-kms | 4/5 | 5/5 |
| 4 | `pam-agentic-access` | infisical-pam | 1/5 | 5/5 |
| 5 | `k8s-operator-v1beta1-autoreload` | infisical-kubernetes-operator | 0/5 | 5/5 |
| 6 | `access-control-describe-vs-read` | infisical-access-control | 3/4 | 4/4 |
| 7 | `scanning-github-radar-connection` | infisical-secret-scanning | 1/4 | 4/4 |
| 8 | `sso-enforcement-breakglass` | infisical-sso | 1/5 | 5/5 |
| 9 | `gateway-ports-no-inbound` | infisical-gateway | 3/5 | 5/5 |

## Notable

**eval-5 (Kubernetes Operator) — baseline 0/5.** Unaided, the model produced the **legacy
`v1alpha1` `InfisicalSecret`** CRD. The current API is `v1beta1` with `InfisicalConnection` /
`InfisicalAuth` / `InfisicalStaticSecret`, and it also omitted the `auto-reload` annotation, so
pods would keep stale values. This is the exact footgun the skill exists to close.

**eval-4 (PAM) and eval-8 (SSO) — baseline 1/5.** These cover product surface the base model has
little knowledge of: agentic access, and the SSO enforcement/break-glass interaction.

**eval-1 (App Connections) — baseline 4/4.** Honest null result: the model already knows the AWS
`assume-role` connection shape including `roleArn` and the External ID requirement. The skill adds
no lift here, and that is worth recording rather than hiding.

**eval-6 (Access Control) — baseline 3/4.** The model already knows `describeSecret` and
`readValue`. The skill's contribution is the nuance that the legacy `read` action grants both.

## Limitations

- Single run per cell; no variance estimate.
- Regex grading checks that correct identifiers appear, not that a whole configuration would deploy.
- Assertions target facts verified from source for these specific skills; this is not a general
  quality measure.
