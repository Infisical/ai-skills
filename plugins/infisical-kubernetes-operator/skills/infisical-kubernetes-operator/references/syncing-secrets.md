# Syncing Secrets into Kubernetes

## InfisicalStaticSecret (v1beta1)

The current way to sync static secrets. Structure: authenticate via a referenced `InfisicalAuth`,
read from one or more **sources**, write to one or more **targets**.

```yaml
apiVersion: secrets.infisical.com/v1beta1
kind: InfisicalStaticSecret
metadata:
  name: my-static-secret
  namespace: default
spec:
  infisicalAuthRef:
    name: my-infisical-auth
    namespace: default
  syncOptions:
    refreshInterval: 60s
  sources:
    - projectId: <your-project-id>
      environmentSlug: dev
      secretPath: /
  targets:
    - name: managed-secret
      namespace: default
      kind: Secret
      creationPolicy: Owner
```

### sources

An array — you can merge several Infisical locations into one target.

| Field | Description |
|-------|-------------|
| `projectId` | The Infisical project |
| `environmentSlug` | Environment slug (`dev`, `staging`, `prod`, …) |
| `secretPath` | Folder path within the environment |

Because `sources` is a list, a common pattern is a shared path plus a service-specific path merged
into one Secret. Be deliberate about collision order when the same key appears in two sources.

### targets

Also an array — the same secrets can be written to several places.

| Field | Description |
|-------|-------------|
| `name` | Name of the Kubernetes object to manage |
| `namespace` | Where to create it |
| `kind` | `Secret` or `ConfigMap` |
| `creationPolicy` | `Owner` or `Orphan` |

**`kind: ConfigMap` writes values in plain text.** Only use it for genuinely non-sensitive
configuration. Defaulting to `Secret` is right.

### creationPolicy

| Value | Behavior |
|-------|----------|
| `Owner` | The operator owns the target object. Deleting the CRD deletes the managed Secret/ConfigMap |
| `Orphan` | The target survives deletion of the CRD |

Default to `Owner` — it keeps cluster state tied to declared state. Use `Orphan` only when something
must keep working through a CRD teardown, and note that it leaves objects behind that nothing
manages.

### refreshInterval

Under `syncOptions`. How often the operator re-reads from Infisical, e.g. `60s`.

Trade-off: shorter means faster propagation and more API calls. Secret endpoints share a rate limit
(see `infisical-api`), so a very short interval multiplied across many CRDs can hit it. `60s` is a
reasonable default; go shorter only where propagation latency genuinely matters.

## Automatic redeployment

**Pods do not reload when a managed Secret or ConfigMap changes.** Without a restart the workload
keeps using stale values — especially when secrets are injected as environment variables, which are
read once at process start.

Add this annotation to the **Deployment, StatefulSet, or DaemonSet** that consumes the object:

```yaml
secrets.infisical.com/auto-reload: "true"
```

Example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
  annotations:
    secrets.infisical.com/auto-reload: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
          envFrom:
            - secretRef:
                name: managed-secret
```

The annotation goes on the **workload**, not on the `InfisicalStaticSecret`. It triggers a rolling
restart when the managed resource updates.

This is the single most-missed step. A user reporting "the secret updated in Infisical but my app
still has the old value" has almost certainly not added this annotation.

Note that with a mounted volume rather than `envFrom`, Kubernetes updates the file on disk
eventually — but only if the application re-reads it. The annotation is still the reliable answer.

## Templating

Rendered output can be templated when the consumer needs a specific format — a full connection
string, an `.env` blob, a config file body.

```yaml
template:
  data:
    ENCODED_SECRET: "{{ .MY_SECRET.Value | encodeBase64 }}"
```

Secrets are addressed as `.SECRET_NAME.Value`.

Helper functions are available, including:

| Helper | Purpose |
|--------|---------|
| `encodeBase64` | Encode a string to base64 (`hello world` → `aGVsbG8gd29ybGQ=`) |
| `decodeBase64ToBytes` | Decode base64 back to the original value |

There is a broad set of helpers beyond these two — check the operator templating snippets in the
docs for the current list rather than guessing at a function name.

Templating is per-API-version: v1beta1 and v1alpha1 have separate templating documentation, so
confirm the version before writing a template.

Typical use — build a connection string from parts:

```yaml
template:
  data:
    DATABASE_URL: "postgresql://{{ .DB_USER.Value }}:{{ .DB_PASS.Value }}@{{ .DB_HOST.Value }}:5432/{{ .DB_NAME.Value }}"
```

This pairs well with `infisical-secret-rotation`, where the username changes on each rotation — the
template rebuilds the URL from the current values rather than hardcoding a user.

## InfisicalSecret (v1alpha1, legacy)

```yaml
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalSecret
metadata:
  name: infisical-secret
```

One resource carries the instance address, authentication, source, and managed-secret target
together. It still works, and it is deprecating.

When advising someone on v1alpha1:

- Answer in v1alpha1 — do not hand them a v1beta1 manifest that will not match the rest of their cluster
- Mention v1beta1 exists and is where new resources should go
- The migration is mechanical: factor the repeated address into one `InfisicalConnection`, the repeated auth into one `InfisicalAuth`, then convert each `InfisicalSecret` into an `InfisicalStaticSecret` with `sources` and `targets`

Do not push a migration unprompted if their setup is working. Do flag it if they are about to add
many new resources.

## Troubleshooting order

1. **Is the operator pod running?** Check its logs.
2. **Does the CRD's status show an auth error?** Most failures are authentication.
3. **Does the source path resolve to anything?** An empty folder produces an empty Secret, not an error.
4. **Does the target Secret exist with the expected keys?**
5. **Did the workload restart?** If the Secret is correct but the app disagrees, it is the `auto-reload` annotation.
6. **Namespace mismatch?** `infisicalAuthRef`, `infisicalConnectionRef`, and target `namespace` are all explicit — a typo silently points at nothing.
