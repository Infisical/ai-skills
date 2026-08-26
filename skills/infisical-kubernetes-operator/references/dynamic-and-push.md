# Dynamic Secrets and Pushing from Kubernetes

Both CRDs on this page are **`v1alpha1`**. They use inline `authentication` blocks rather than the
v1beta1 `InfisicalConnection` / `InfisicalAuth` split.

## InfisicalDynamicSecret

Creates and maintains a dynamic secret **lease** from inside the cluster, writing the generated
credentials into a Kubernetes Secret. The operator renews the lease before it expires.

```yaml
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalDynamicSecret
metadata:
  name: infisicaldynamicsecret
spec:
  hostAPI: https://app.infisical.com/api   # Optional, this is the default

  dynamicSecret:
    secretName: <dynamic-secret-name>
    projectId: <project-id>
    secretsPath: <path/to/dynamic-secret>  # Root directory is /
    environmentSlug: <env-slug>

  leaseRevocationPolicy: Revoke
  leaseTTL: 1m

  managedSecretReference:
    secretName: <secret-name>
    secretNamespace: default
    creationPolicy: Orphan

  authentication:
    kubernetesAuth:
      identityId: <machine-identity-id>
      serviceAccountRef:
        name: <service-account-name>
        namespace: <service-account-namespace>
```

### Constraints that bite

- **`hostAPI` includes `/api`.** It is `https://app.infisical.com/api`, not the bare domain. Other CRDs and the CLI take a bare address; this one does not.
- **`leaseTTL` must be under 1 day**, and must be below the dynamic secret's Max TTL if one is set. A `leaseTTL` above the Max TTL fails.
- **`managedSecretReference.secretNamespace` must match the CRD's own namespace.** Cross-namespace targets are not allowed here, unlike `InfisicalStaticSecret` targets.
- **Define exactly one authentication method.** The docs list all the options together for reference; leaving more than one in place causes authentication problems. Delete all but the one you use.

### leaseRevocationPolicy

| Value | Behavior on CRD deletion |
|-------|-------------------------|
| `Revoke` | Leases created by the operator are revoked |
| (unset) | Leases are left to expire on their own |

Use `Revoke`. Otherwise deleting the CRD leaves live database credentials in existence until their
TTL runs out, with nothing tracking them.

### Choosing this over the alternatives

| Approach | When |
|----------|------|
| `InfisicalDynamicSecret` | The app reads credentials from a Kubernetes Secret and you want them ephemeral |
| Infisical Agent with `dynamicSecret` template | The app reads a file, or you need a specific file format. See `infisical-agent` |
| SDK calling the lease API | The app is lease-aware and can handle renewal itself |

The operator route is best when you cannot change the application — it keeps a normal Kubernetes
Secret populated with credentials that happen to be short-lived.

Remember the pod still needs restarting to pick up a renewed credential if it reads env vars —
`secrets.infisical.com/auto-reload: "true"` on the workload, as with static secrets.

## InfisicalPushSecret

The reverse direction: takes an existing **Kubernetes** Secret and pushes its contents **into**
Infisical.

```yaml
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalPushSecret
metadata:
  name: infisical-push-secret-demo
spec:
  resyncInterval: 1m       # Remove to disable automatic reconciliation
  hostAPI: https://app.infisical.com/api

  updatePolicy: Replace    # Optional, defaults to no replacement
  deletionPolicy: Delete   # Optional, defaults to no deletion

  destination:
    projectId: <project-id>        # Either projectId or projectSlug
    projectSlug: <project-slug>
    environmentSlug: <env-slug>
    secretsPath: <secret-path>

  push:
    secret:
      secretName: push-secret-demo
      secretNamespace: default

  authentication:
    kubernetesAuth:
      identityId: <machine-identity-id>
      serviceAccountRef:
        name: <service-account-name>
        namespace: <service-account-namespace>
```

### Policies

| Field | Value | Behavior | Default |
|-------|-------|----------|---------|
| `updatePolicy` | `Replace` | Existing secrets in Infisical are overwritten on sync | No replacement |
| `deletionPolicy` | `Delete` | Operator-managed secrets in Infisical are deleted when the CRD is deleted | No deletion |

Both default to the **safe, non-destructive** behavior. Be explicit about what enabling them does:

- `updatePolicy: Replace` means the cluster becomes the source of truth for those keys. Anything edited in the Infisical UI gets overwritten on the next resync.
- `deletionPolicy: Delete` means removing a CRD removes secrets from Infisical. That is real data loss if someone deletes the CRD carelessly.

Leave them unset unless the user specifically wants those semantics.

### resyncInterval

Remove the field entirely to disable automatic reconciliation — then the push happens only when the
CRD changes. Useful for a one-time migration where you do not want the cluster continuously
asserting itself over Infisical.

### `projectId` or `projectSlug`

`destination` accepts either. Supply one, not both.

### When to use it

Honest framing: pushing from Kubernetes inverts the normal direction, where Infisical is the source
of truth. Legitimate uses:

- **Migration.** You have secrets in Kubernetes today and want them in Infisical. Push once with `resyncInterval` removed, then switch to syncing the other way.
- **A cluster-side generator.** Something in-cluster mints a value (a cert, a generated token) and other systems need it from Infisical.

If a user's plan is to keep secrets authored in Kubernetes manifests permanently and mirror them
into Infisical, push back gently: that leaves the secrets in git and gives up most of what Infisical
provides. The usual answer is to move authorship into Infisical and sync inward with
`InfisicalStaticSecret`.

### Do not create a loop

Never point an `InfisicalPushSecret` at the same path an `InfisicalStaticSecret` reads from and
writes into. The two controllers will fight, each overwriting the other on its own interval.

## Authentication in v1alpha1

Both CRDs accept the same set of inline methods under `authentication`:

| Block | Notes |
|-------|-------|
| `kubernetesAuth` | `identityId` + `serviceAccountRef`. **Preferred** |
| `awsIamAuth` | `identityId` |
| `azureAuth` | `identityId` |
| `gcpIamAuth` | `identityId` + `serviceAccountKeyFilePath` |
| `gcpIdTokenAuth` | `identityId` |
| `universalAuth` | Client ID / secret via a referenced Secret |

**Exactly one.** The published examples show every block at once purely as a reference; copying that
verbatim leaves several methods defined and authentication becomes unpredictable. Always strip it
down to one before applying.
