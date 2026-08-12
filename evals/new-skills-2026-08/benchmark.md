# New Skills — A/B Eval

Iteration `new-skills-2026-08` · ground truth `Infisical/infisical@bbe1f02208` ·
model `claude-sonnet-5` · tools **disabled** · deterministic regex grading.

One eval per newly added skill, plus three for the App Connection API surface added afterwards.
Every assertion tests a fact verified against the Infisical source.

## Results

| Arm | Score | Pass rate |
|---|---|---|
| No skill | 27/56 | **48.2%** |
| With new skill | 56/56 | **100.0%** |

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
| 10 | `appconn-discovery-endpoint-auth` | infisical-app-connections | 1/3 | 3/3 |
| 11 | `appconn-credentials-okta-datadog` | infisical-app-connections | 3/4 | 4/4 |
| 12 | `appconn-lookup-by-name` | infisical-app-connections | 2/3 | 3/3 |

## Notable

**eval-10 (App Connection discovery auth) — baseline 1/3.** Asked to script a call that lists KMS
keys on an AWS connection, the unaided model writes it as a normal API call. It is not: 88 of the 94
discovery endpoints are `AuthMode.JWT` only and reject a machine identity token. Unaided, the model
produces a script that cannot work, and the failure surfaces only at runtime as a 401.

**eval-5 (Kubernetes Operator) — baseline 0/5.** Unaided, the model produced the legacy `v1alpha1`
`InfisicalSecret` CRD. Current is `v1beta1` with `InfisicalConnection` / `InfisicalAuth` /
`InfisicalStaticSecret`, and it also omitted the `auto-reload` annotation, so pods keep stale values.

**eval-4 (PAM) and eval-8 (SSO) — baseline 1/5.** Product surface the base model barely knows:
agentic access, and the SSO enforcement / break-glass interaction.

**eval-1 (App Connections, AWS) — baseline 4/4.** Honest null result: the model already knows the
`assume-role` shape including `roleArn` and the External ID requirement. Recorded rather than hidden.

**eval-6 (Access Control) — baseline 3/4.** The model already knows `describeSecret` and `readValue`.
The skill's contribution is that the legacy `read` action grants both.

## Limitations

- Single run per cell; no variance estimate.
- Regex grading checks that correct identifiers appear, not that a whole configuration deploys.
- Assertions target facts verified from source for these specific skills; not a general quality measure.
