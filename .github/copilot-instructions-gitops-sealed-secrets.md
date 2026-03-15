# Copilot Instructions – Implement Kubernetes Sealed Secrets for PostgreSQL

## Goal

Introduce **Bitnami Sealed Secrets** to securely manage Kubernetes secrets in the GitOps repository.

The current repository contains a **plaintext Kubernetes Secret** for PostgreSQL credentials.
This must be replaced with a **SealedSecret** so that encrypted credentials can safely be stored in Git.

The deployment is managed via **FluxCD and Kustomize**.

---

# Background

GitOps repositories should **never contain plaintext credentials**.

Sealed Secrets solves this by:

1. Encrypting secrets locally using the `kubeseal` CLI
2. Storing the encrypted object (`SealedSecret`) in Git
3. Allowing the **Sealed Secrets Controller** in the Kubernetes cluster to decrypt the secret and create a standard Kubernetes `Secret`.

Only the controller inside the cluster has the **private key**.

---

# Current Repository Structure

```
infrastructure
└── clusters
    └── dev
        ├── database
        │   └── postgresql
        │       ├── kustomization.yaml
        │       ├── namespace.yaml
        │       ├── pvc.yaml
        │       ├── secret.yaml
        │       ├── service.yaml
        │       └── statefulset.yaml
        ├── flux-system
        │   ├── gotk-components.yaml
        │   ├── gotk-sync.yaml
        │   ├── kustomization.yaml
        │   └── README.md
        └── kustomization.yaml
```

---

# Target Repository Structure

The repository should be reorganized slightly to introduce an **apps directory** and an **infrastructure directory**.

```
infrastructure
└── clusters
    └── dev
        ├── infrastructure
        │   └── sealed-secrets
        │       ├── helmrepository.yaml
        │       ├── helmrelease.yaml
        │       └── kustomization.yaml
        │
        ├── apps
        │   └── postgresql
        │       ├── kustomization.yaml
        │       ├── namespace.yaml
        │       ├── pvc.yaml
        │       ├── sealed-secret.yaml
        │       ├── service.yaml
        │       └── statefulset.yaml
        │
        ├── flux-system
        │   └── ...
        │
        └── kustomization.yaml
```

---

# Implementation Steps

Follow the steps in the **exact order below**.

Each step corresponds to a **single Git commit**.

Test and verify each step before proceeding to the next.

---

# Commit 1 — Reorganize Repository Structure

Commit message:

```
refactor: move postgres manifests to apps directory and update kustomization paths
```

Tasks:

1. Rename the directory:

```
clusters/dev/database/postgresql
```

to

```
clusters/dev/apps/postgresql
```

2. Update all references in:

```
clusters/dev/kustomization.yaml
```

Replace:

```
database/postgresql
```

with:

```
apps/postgresql
```

3. Ensure the cluster kustomization still references the PostgreSQL manifests.

Example:

```yaml
resources:
  - apps/postgresql
```

---

# Commit 2 — Install Sealed Secrets Controller

Commit message:

```
feat: install sealed-secrets controller via Flux
```

Create directory:

```
clusters/dev/infrastructure/sealed-secrets
```

---

## helmrepository.yaml

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: sealed-secrets
  namespace: flux-system
spec:
  interval: 1h
  url: https://bitnami-labs.github.io/sealed-secrets
```

---

## helmrelease.yaml

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: sealed-secrets
  namespace: kube-system
spec:
  interval: 1h
  chart:
    spec:
      chart: sealed-secrets
      version: ">=2.0.0"
      sourceRef:
        kind: HelmRepository
        name: sealed-secrets
        namespace: flux-system
  install:
    crds: Create
```

---

## kustomization.yaml

```yaml
resources:
  - helmrepository.yaml
  - helmrelease.yaml
```

---

# Commit 3 — Register Infrastructure in Cluster

Commit message:

```
feat: register sealed-secrets infrastructure in dev cluster
```

Edit:

```
clusters/dev/kustomization.yaml
```

Example:

```yaml
resources:
  - infrastructure/sealed-secrets
  - apps/postgresql
```

This ensures Flux installs the controller.

---

# Commit 4 — Add Sealed Secret for PostgreSQL

Commit message:

```
feat: add sealed secret for postgres credentials
```

---

## Install kubeseal locally

```
brew install kubeseal
```

or

```
wget https://github.com/bitnami-labs/sealed-secrets/releases/latest/download/kubeseal-linux-amd64
```

---

## Fetch the cluster public certificate

```
kubeseal --fetch-cert \
  --controller-name sealed-secrets \
  --controller-namespace kube-system \
  > sealed-secrets-cert.pem
```

---

## Convert the existing secret

Take the existing file:

```
apps/postgresql/secret.yaml
```

Example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: database
type: Opaque
stringData:
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: supersecret
```

Convert it:

```
kubeseal \
  --format yaml \
  --cert sealed-secrets-cert.pem \
  < secret.yaml \
  > sealed-secret.yaml
```

---

## Resulting sealed-secret.yaml

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: postgres-secret
  namespace: database
spec:
  encryptedData:
    POSTGRES_USER: Ag...
    POSTGRES_PASSWORD: Ag...
```

Place the file in:

```
clusters/dev/apps/postgresql/sealed-secret.yaml
```

---

# Commit 5 — Remove Plaintext Secret

Commit message:

```
refactor: replace plaintext postgres secret with sealed secret
```

Tasks:

Delete:

```
apps/postgresql/secret.yaml
```

Update:

```
apps/postgresql/kustomization.yaml
```

Example:

```yaml
resources:
  - namespace.yaml
  - pvc.yaml
  - sealed-secret.yaml
  - service.yaml
  - statefulset.yaml
```

---

# Verification Steps

After pushing the changes, Flux should deploy the controller and apply the SealedSecret.

Verify the resources:

```
kubectl get sealedsecret -A
```

Check if the secret was created:

```
kubectl get secret -n database
```

Expected result:

```
postgres-secret
```

---

# Security Considerations

Never commit plaintext secrets to Git.

Always follow this workflow:

```
create secret locally
↓
encrypt with kubeseal
↓
commit sealed secret
↓
delete plaintext secret
```

---

# Disaster Recovery

Backup the controller private key:

```
kubectl get secret -n kube-system sealed-secrets-key -o yaml > sealed-secrets-backup.yaml
```

Without this key, previously sealed secrets cannot be decrypted.

---
