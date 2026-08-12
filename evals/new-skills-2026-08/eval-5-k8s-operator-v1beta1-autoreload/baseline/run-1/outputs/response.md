Here are the manifests. This uses two pieces: the Infisical Operator's `InfisicalSecret` CRD to sync from Infisical into a native Kubernetes `Secret`, and `Reloader` to make your Deployment restart automatically whenever that Secret's contents change (Kubernetes itself does not restart pods on Secret updates, even when mounted as env vars).

**Prerequisites (one-time, cluster-level):**

```
helm repo add infisical-helm-charts https://dl.cloudsmith.io/public/infisical/helm-charts/helm/charts
helm install infisical-operator infisical-helm-charts/secrets-operator \
  --namespace infisical-operator-system --create-namespace

helm repo add stakater https://stakater.github.io/stakater-charts
helm install reloader stakater/reloader --namespace kube-system
```

**1. Machine Identity credentials** (create a Machine Identity in your Infisical org, enable Universal Auth on it, grant it read access to the project/environment, then store its clientId/clientSecret here):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: universal-auth-credentials
  namespace: default
type: Opaque
stringData:
  clientId: <machine-identity-client-id>
  clientSecret: <machine-identity-client-secret>
```

**2. InfisicalSecret CR** — pulls secrets from Infisical and keeps a managed Kubernetes Secret in sync:

```yaml
apiVersion: secrets.infisical.com/v1alpha1
kind: InfisicalSecret
metadata:
  name: my-app-secrets
  namespace: default
spec:
  hostAPI: https://app.infisical.com/api   # omit or point at your self-hosted instance
  resyncInterval: 60                       # seconds between polls for changes
  authentication:
    universalAuth:
      secretsScope:
        projectSlug: my-project-a1b2
        envSlug: prod
        secretsPath: "/"
        recursive: true
      credentialsRef:
        secretName: universal-auth-credentials
        secretNamespace: default
  managedSecretReference:
    secretName: my-app-managed-secret
    secretNamespace: default
    creationPolicy: "Owner"                # operator owns and cleans up the Secret
```

**3. Deployment** — the `reloader.stakater.com/auto: "true"` annotation tells Reloader to watch every Secret/ConfigMap this pod spec references and roll the Deployment when any of them change:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
  annotations:
    reloader.stakater.com/auto: "true"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: my-app:latest
          envFrom:
            - secretRef:
                name: my-app-managed-secret
```

How it flows end to end: the operator polls Infisical every `resyncInterval` seconds and writes any changes into `my-app-managed-secret`. Reloader watches that Secret, and on any change computes a new hash and patches it onto the pod template annotations, which triggers a normal rolling restart, so new pods start with the updated env vars.

A couple of notes worth flagging:

- `universalAuth` requires a static `clientSecret` sitting in a cluster Secret. If you'd rather avoid that, the operator also supports `kubernetesAuth`, which authenticates using the pod's own ServiceAccount token against a Machine Identity, with no static secret to manage. Say the word if you want that variant instead.
- If you don't want a full pod restart on every secret change (for apps that hot reload config from disk), you can skip Reloader and instead mount the managed Secret as a volume, since kubelet updates mounted Secret volumes in place on a poll interval.
