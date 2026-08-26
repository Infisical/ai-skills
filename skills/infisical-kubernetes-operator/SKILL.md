---
name: infisical-kubernetes-operator
description: "Guide for the Infisical Kubernetes Operator — syncing secrets from Infisical into Kubernetes Secrets and ConfigMaps, pushing secrets from Kubernetes to Infisical, and managing dynamic secret leases in-cluster. Covers the v1beta1 CRDs (InfisicalConnection, InfisicalAuth, InfisicalStaticSecret) and the legacy v1alpha1 CRDs (InfisicalSecret, InfisicalDynamicSecret, InfisicalPushSecret), Helm installation cluster-wide or namespace-scoped, all 7 operator auth methods, sources and targets, creationPolicy Owner vs Orphan, refreshInterval, the secrets.infisical.com/auto-reload annotation for automatic Deployment rollouts, and Go templating of rendered secrets. Use this skill when someone asks about: Infisical Kubernetes Operator, InfisicalSecret CRD, InfisicalStaticSecret, syncing Infisical secrets into a Kubernetes Secret, auto-reloading pods on secret change, pushing Kubernetes secrets to Infisical, or 'how do I get Infisical secrets into my Kubernetes cluster'. Not for self-hosting Infisical on Kubernetes (infisical-self-host) — that is a different Helm chart — nor for rendering secrets to files (infisical-agent)."
---
# Infisical Kubernetes Operator Guide

You are a setup assistant helping users run the Infisical Kubernetes Operator — a set of
controllers that keep Kubernetes Secrets and ConfigMaps in step with Infisical, push secrets the
other way, and manage dynamic secret leases in-cluster.

## The first question: which API version

**The operator supports two CRD API versions, and they have different object models.**

| Version | Status | Use for |
|---------|--------|---------|
| `secrets.infisical.com/v1beta1` | **Current** | All new installations |
| `secrets.infisical.com/v1alpha1` | **Legacy, deprecating soon** | Existing installs only |

This is the single most important thing to establish before writing any YAML. The two versions are
not interchangeable:

- **v1alpha1** is monolithic — one `InfisicalSecret` resource carries the instance address, the authentication, the source, and the target.
- **v1beta1** splits those concerns into three resources: `InfisicalConnection` (where Infisical is), `InfisicalAuth` (how to authenticate), and `InfisicalStaticSecret` (what to sync where).

If a user pastes an `InfisicalSecret` manifest, they are on v1alpha1. Answer in the version they are
using, and mention that v1beta1 is where new work should go — but do not silently rewrite their
manifest into the other version.

## The CRDs

| Kind | API version | Purpose |
|------|-------------|---------|
| `InfisicalConnection` | v1beta1 | Points at an Infisical instance |
| `InfisicalAuth` | v1beta1 | How to authenticate, referencing a connection |
| `InfisicalStaticSecret` | v1beta1 | Sync static secrets into Secrets/ConfigMaps |
| `InfisicalSecret` | v1alpha1 | Legacy all-in-one sync resource |
| `InfisicalDynamicSecret` | v1alpha1 | Manage a dynamic secret lease in-cluster |
| `InfisicalPushSecret` | v1alpha1 | Push secrets from Kubernetes to Infisical |

Note `InfisicalDynamicSecret` and `InfisicalPushSecret` are documented at **v1alpha1** even though
static secret syncing has moved to v1beta1. Do not assume every CRD has a v1beta1 form.

## Not this skill

| If the user wants... | Use |
|----------------------|-----|
| Secrets rendered to a **file** in a pod, or a sidecar/init container | `infisical-agent` |
| The CLI wrapping a process (`infisical run`) | `infisical-setup` |
| To set up **Kubernetes Auth** for a machine identity in general | `infisical-setup` |
| To encrypt **etcd** with an Infisical key | `infisical-kms` |
| To self-host Infisical itself on Kubernetes | `infisical-self-host` |
| To push secrets to a non-Kubernetes third party | `infisical-secret-syncs` |

Distinguish the operator from the agent. The **operator** manages Kubernetes API objects — Secrets
and ConfigMaps — cluster-wide from a controller. The **agent** runs alongside your app and writes
files into its filesystem. If the app reads env vars from a Secret, use the operator. If it reads a
config file, use the agent.

Also distinguish from self-hosting: installing the *operator* via Helm is not installing *Infisical*
via Helm. Both use the same Cloudsmith Helm repo, which causes confusion.

## How to use this skill

1. **Establish v1beta1 vs v1alpha1**
2. **Install the operator** — cluster-wide or namespace-scoped
3. **Choose an auth method** — prefer `kubernetes` (zero static credentials)
4. **Define sources** (what to read from Infisical) and **targets** (what to write in-cluster)
5. **Set `refreshInterval`** and decide on `creationPolicy`
6. **Wire up reload** so workloads actually pick up changes
7. **Add templating** if the target needs a specific format

## Reference files

| File | When to read |
|------|-------------|
| `references/install-and-auth.md` | Helm install (cluster-wide and namespace-scoped), supported Kubernetes versions, all 7 auth methods, InfisicalConnection and InfisicalAuth |
| `references/syncing-secrets.md` | InfisicalStaticSecret and legacy InfisicalSecret, sources/targets, creationPolicy, refreshInterval, auto-reload, templating |
| `references/dynamic-and-push.md` | InfisicalDynamicSecret leases in-cluster, InfisicalPushSecret for Kubernetes → Infisical |

## Guiding principles

- **Ask which API version before writing YAML.** Getting this wrong produces manifests the cluster rejects.
- **Prefer `method: kubernetes`.** The pod's service account token authenticates it; nothing static is stored in the cluster. Fall back to `universal` only where Kubernetes Auth cannot be configured.
- **A synced Secret does not restart anything by itself.** Add the `secrets.infisical.com/auto-reload: "true"` annotation to dependent Deployments, or nothing picks up the new value until the next rollout.
- **`creationPolicy` decides ownership.** `Owner` ties the managed Secret's lifecycle to the CRD; `Orphan` leaves it behind on delete. Default to `Owner` unless something else must survive.
- **Namespace-scoped installs: only the first installs CRDs.** CRDs are cluster-wide, so subsequent installs must set `installCRDs: false` or they conflict.
- **Never put a client secret in a manifest.** Credentials go in a Kubernetes Secret that the CRD references, not inline.
- **Consider External Secrets Operator** if the user already runs it — Infisical has a provider there, and adding a second secrets operator is rarely worth it.
