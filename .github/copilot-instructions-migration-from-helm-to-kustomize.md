# Copilot Instructions – Migrate from Helm + Kustomize to Pure Kustomization

## Goal

Remove Helm-based deployment for PostgreSQL and replace it with a **pure Kustomize deployment using plain Kubernetes manifests** managed by FluxCD, version 2.8.1.

After the migration:

* PostgreSQL will be deployed using **StatefulSet + Service + PersistentVolumeClaim**
* Flux will reconcile the manifests through **Kustomization resources**
* HelmRepository, HelmRelease, and Helm secrets will no longer be used.

This simplifies the GitOps workflow and improves debugging by relying only on Kubernetes primitives.

---

# Target Architecture

Git Repository
→ Flux GitRepository
→ Flux Kustomization
→ Kubernetes manifests

PostgreSQL resources deployed:

* Namespace
* Secret
* Service
* PersistentVolumeClaim
* StatefulSet

---

# Repository Structure After Migration

Restructure the database manifests into a dedicated folder.

```
infrastructure
└── clusters
    └── dev
        ├── flux-system
        │   ├── gotk-components.yaml
        │   ├── gotk-sync.yaml
        │   ├── kustomization.yaml
        │   └── README.md
        │
        ├── database
        │   └── postgresql
        │       ├── namespace.yaml
        │       ├── secret.yaml
        │       ├── service.yaml
        │       ├── pvc.yaml
        │       ├── statefulset.yaml
        │       └── kustomization.yaml
        │
        └── kustomization.yaml
```

The existing `helm/` directory will be removed.

---

# Step 1 – Remove Helm Resources

Delete the entire Helm directory:

```
clusters/dev/helm/
```

This removes:

* HelmRepository definitions
* HelmRelease definitions
* Helm-specific secrets
* Helm Kustomization references

Flux should no longer manage any Helm charts.

---

# Step 2 – Create PostgreSQL Manifests

Create a new directory:

```
clusters/dev/database/postgresql
```

Add the following Kubernetes resources:

1. namespace.yaml
2. secret.yaml
3. service.yaml
4. pvc.yaml
5. statefulset.yaml

---

# Step 3 – Example Secret

The database credentials must be stored in a Kubernetes Secret.

```
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-auth
  namespace: telemetry-database-dev
type: Opaque
stringData:
  postgres-password: examplepassword
  password: examplepassword
```

---

# Step 4 – Example PostgreSQL StatefulSet

Use the official PostgreSQL container image.

```
image: postgres:16
```

Important configuration:

* mount data at `/var/lib/postgresql/data`
* reference the secret for passwords
* request persistent storage

---

# Step 5 – Create PostgreSQL Kustomization

File:

```
clusters/dev/database/postgresql/kustomization.yaml
```

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yaml
  - secret.yaml
  - service.yaml
  - pvc.yaml
  - statefulset.yaml
```

---

# Step 6 – Update Cluster Kustomization

Edit:

```
clusters/dev/kustomization.yaml
```

Remove Helm references and add the database directory.

Example:

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - flux-system
  - database/postgresql
```

---

# Step 7 – Flux Reconciliation

Flux will automatically detect the new manifests.

Manual reconciliation commands:

```
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

Verify deployment:

```
kubectl get pods -n telemetry-database-dev
```

Expected:

```
postgresql-0   Running
```

---

# Design Principles

Follow these guidelines when adding Kubernetes resources:

1. Prefer **native Kubernetes resources over Helm charts**.
2. Use **Kustomize for composition**, not templating logic.
3. Store secrets in Kubernetes Secrets (or integrate with a secret manager later).
4. Use **StatefulSets for databases**.
5. Keep database manifests isolated in a dedicated directory.

---

# Future Improvements

After the migration, consider adding:

* readiness and liveness probes
* resource limits
* PostgreSQL configuration via ConfigMap
* backup jobs
* monitoring via Prometheus exporter

---

# Expected Outcome

Flux manages the following flow:

```
Git Repository
      ↓
Flux Kustomization
      ↓
PostgreSQL Kubernetes Resources
```

No Helm controllers are required for the PostgreSQL deployment.
