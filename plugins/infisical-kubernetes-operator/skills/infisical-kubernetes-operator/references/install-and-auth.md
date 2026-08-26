# Installing the Operator and Configuring Auth

## Supported versions

**Kubernetes minor releases** officially supported (the latest operator is tested against each):

1.33, 1.32, 1.31, 1.30, 1.29

**Distributions** tested successfully:

- Amazon EKS
- Google GKE
- Microsoft AKS
- Oracle OKE
- Red Hat OpenShift

Other versions and distributions may work but are not officially supported.

## Installation

The operator is installed with Helm from the Cloudsmith chart repository. The chart is
`secrets-operator`.

```bash
helm repo add infisical-helm-charts 'https://dl.cloudsmith.io/public/infisical/helm-charts/helm/charts/'
helm repo update
```

Note this is the **same Helm repo** used to self-host Infisical itself, but a different chart.
`secrets-operator` installs the operator; the standalone chart installs the platform. Do not confuse
them.

### Cluster-wide (default)

The operator watches and manages CRDs across all namespaces. Quickest way to start.

```bash
helm install --generate-name infisical-helm-charts/secrets-operator
```

### Namespace-scoped

Restricts the operator's permissions to specific namespaces. Use for multi-tenant clusters or where
strict resource isolation is required.

Single namespace:

```bash
helm install operator-namespaced infisical-helm-charts/secrets-operator \
  --namespace single-namespace \
  --set scopedNamespaces=single-namespace \
  --set scopedRBAC=true
```

Equivalent `values.yaml`:

```yaml
scopedNamespaces: single-namespace
scopedRBAC: true
installCRDs: true
```

### Multiple namespace-scoped installs

**CRDs are cluster-wide resources, so only the first install may create them.** Every subsequent
install must set `installCRDs: false` or they conflict.

```bash
helm install operator-1 infisical-helm-charts/secrets-operator \
  --namespace ns1 \
  --set scopedNamespaces=ns1 \
  --set scopedRBAC=true \
  --set installCRDs=true    # first install creates the CRDs (default is true)

helm install operator-namespace2 infisical-helm-charts/secrets-operator \
  --namespace ns2 \
  --set scopedNamespaces=ns2 \
  --set scopedRBAC=true \
  --set installCRDs=false   # subsequent installs must NOT reinstall CRDs
```

This is the most common namespace-scoped mistake. Symptom: the second `helm install` fails on
already-existing CRDs, or upgrades fight over CRD ownership.

## v1beta1 auth architecture

v1beta1 splits configuration into three resources. Create them in this order.

### 1. InfisicalConnection — where Infisical is

```yaml
apiVersion: secrets.infisical.com/v1beta1
kind: InfisicalConnection
metadata:
  name: my-infisical-connection
  namespace: default
spec:
  address: https://app.infisical.com
```

Set `address` to your own domain for self-hosted instances. One connection can be referenced by many
`InfisicalAuth` resources.

### 2. InfisicalAuth — how to authenticate

```yaml
apiVersion: secrets.infisical.com/v1beta1
kind: InfisicalAuth
metadata:
  name: my-infisical-auth
  namespace: default
spec:
  infisicalConnectionRef:
    name: my-infisical-connection
    namespace: default
  method: kubernetes
  kubernetes:
    identityIdRef:
      name: kubernetes-credentials
      namespace: default
      key: identityId
    serviceAccountRef:
      name: infisical-service-account
      namespace: default
```

Note the pattern: identifiers come from **`*Ref` fields pointing at Kubernetes Secrets**, not inline
values. `identityIdRef` names a Secret plus the `key` within it. Keep credentials out of manifests.

### 3. Then a sync resource

`InfisicalStaticSecret` references the `InfisicalAuth` via `infisicalAuthRef`. See
`references/syncing-secrets.md`.

## The 7 auth methods

`spec.method` on `InfisicalAuth`:

| `method` | Platform | Static credentials in cluster? |
|----------|----------|-------------------------------|
| `kubernetes` | Any Kubernetes cluster | **No** — uses the pod service account token |
| `aws-iam` | EKS / AWS | No — uses the IAM role |
| `azure` | AKS / Azure | No — uses managed identity |
| `gcp-id-token` | GKE / GCP | No — uses the GCP identity token |
| `gcp-iam` | GCP | A service account key |
| `ldap` | LDAP/AD environments | Bind credentials |
| `universal` | Anywhere | Client ID + Client Secret |

**Prefer `kubernetes`.** It is the platform-native, zero-static-credential option and works on every
distribution. There is no reason to use `universal` in a cluster where Kubernetes Auth can be
configured.

Rough ordering when advising:

1. `kubernetes` — always the first choice in-cluster
2. `aws-iam` / `azure` / `gcp-id-token` — if the workload's cloud identity is already the trust anchor
3. `universal` — last resort

### Kubernetes Auth prerequisites

Kubernetes Auth requires a token reviewer configured on the machine identity in Infisical, plus a
service account in the cluster whose token the operator presents. Setting up the identity side is
covered in `infisical-setup` under Kubernetes Auth.

The `serviceAccountRef` in `InfisicalAuth` names the service account whose token is used — it must
match what the machine identity's Kubernetes Auth config permits (allowed namespaces and service
account names), or authentication is rejected.

### Universal Auth

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: infisical-universal-auth
  namespace: default
stringData:
  clientId: "<machine-identity-client-id>"
  clientSecret: "<machine-identity-client-secret>"
```

Then reference that Secret from the `InfisicalAuth` resource rather than inlining the values.

Never write a client secret directly into an `InfisicalAuth` manifest — manifests end up in git.

## v1alpha1 auth

In v1alpha1 there are no separate connection and auth resources; authentication is configured inline
on the `InfisicalSecret` resource itself, along with the instance address. That coupling is why
v1beta1 exists — a connection and auth config had to be repeated on every synced secret.

When migrating, factor the repeated address and auth out into one `InfisicalConnection` and one
`InfisicalAuth`, then point each `InfisicalStaticSecret` at the auth.

## Verifying

After installing and applying the CRDs:

1. Check the operator pod is running in its namespace
2. Check the CRD's status for authentication errors — the operator reports failures on the resource
3. Confirm the target Secret exists and holds the expected keys

If the target Secret never appears, the failure is almost always authentication or a source path that
resolves to nothing. Read the CRD's status conditions before anything else.
