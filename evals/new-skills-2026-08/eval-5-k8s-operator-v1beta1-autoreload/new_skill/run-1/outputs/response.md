Sync via v1beta1 needs three resources (connection, auth, static secret) plus the auto-reload annotation on the Deployment. Here are the manifests, using `kubernetes` auth since it requires no static credentials in-cluster.

**1. InfisicalConnection** — where Infisical is

```yaml
apiVersion: secrets.infisical.com/v1beta1
kind: InfisicalConnection
metadata:
  name: my-infisical-connection
  namespace: default
spec:
  address: https://app.infisical.com
```

**2. InfisicalAuth** — how to authenticate (Kubernetes Auth, no static credentials)

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

`identityIdRef` points at a Kubernetes Secret holding the machine identity ID, not an inline value. That Secret needs to exist separately:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kubernetes-credentials
  namespace: default
stringData:
  identityId: "<machine-identity-id>"
```

**3. InfisicalStaticSecret** — the sync itself

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

**4. Deployment** — with `auto-reload` so it rolls when the secret changes

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

A few things to fill in before applying: your real Infisical instance address (or omit `address` for the default cloud one), the machine identity ID, the project ID, and the service account whose token the identity's Kubernetes Auth config actually allows. The service account itself (`infisical-service-account`) also needs to exist in the `default` namespace.

Once applied, verify in this order: operator pod running, `InfisicalStaticSecret` status shows no auth errors, `managed-secret` exists with expected keys, and the Deployment rolls on updates because of the annotation.
