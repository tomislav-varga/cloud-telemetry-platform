# Copilot Instructions – PostgreSQL Deployment using FluxCD

## Goal

Deploy the PostgreSQL database for the telemetry platform using **GitOps with FluxCD**.

Do not create a custom database Docker image.

Instead, deploy PostgreSQL using the **Bitnami PostgreSQL Helm chart** managed by FluxCD.

---

# Deployment Architecture

The database will run inside Kubernetes as a **StatefulSet** created by a Helm chart.

The deployment flow:

Git Repository
→ FluxCD reads manifests
→ Flux installs Helm chart
→ Helm deploys PostgreSQL
→ PostgreSQL runs as StatefulSet with persistent storage

---

# Repository Structure

Infrastructure manifests should be stored in the repository under:

```
infrastructure/
  kubernetes/
    postgres/
        namespace.yaml
        helmrepository.yaml
        helmrelease.yaml
```

Copilot should generate manifests that follow this structure.

---

# Namespace

PostgreSQL must run in a dedicated namespace:

```
telemetry-database
```

Copilot should create a Kubernetes namespace manifest.

---

# Helm Repository

Use the Bitnami Helm repository.

HelmRepository configuration:

```
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.bitnami.com/bitnami
```

FluxCD will pull charts from this repository.

---

# PostgreSQL Helm Chart

Use the Bitnami PostgreSQL chart.

Chart name:

```
postgresql
```

Example chart source:

```
bitnami/postgresql
```

---

# HelmRelease

The HelmRelease manifest defines how PostgreSQL is deployed.

Important configuration values:

### Database Name

```
telemetry
```

### Username

```
telemetry_user
```

### Password

Must be stored in a **Kubernetes Secret**, not in plain YAML.

---

# Persistence

PostgreSQL must use persistent storage.

Configuration requirements:

* persistence enabled
* storage class defined by cluster
* recommended size: 10Gi

Example configuration:

```
persistence:
  enabled: true
  size: 10Gi
```

---

# Security

Credentials must not be hardcoded.

Passwords must be provided through:

```
Kubernetes Secret
```

Copilot should generate a secret manifest placeholder.

---

# Resource Limits

PostgreSQL should have resource requests and limits.

Example:

```
resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1
    memory: 1Gi
```

---

# Kubernetes Compatibility

The deployment must support:

* readiness probes
* liveness probes
* persistent volumes
* rolling upgrades

The Bitnami Helm chart already provides these capabilities.

---

# Integration with Backend

The FastAPI backend will connect to PostgreSQL using an environment variable:

```
DATABASE_URL
```

Example format:

```
postgresql://telemetry_user:<password>@postgresql.telemetry-database.svc.cluster.local:5432/telemetry
```

---

# GitOps Best Practices

Copilot must follow these rules:

1. Infrastructure must be defined declaratively in Git
2. FluxCD controllers must manage reconciliation
3. Do not manually modify running Kubernetes resources
4. All configuration must be stored in the repository
5. Images and charts must be versioned

---

# What Copilot Should Generate

Copilot should generate the following manifests:

1. Namespace manifest
2. HelmRepository manifest
3. HelmRelease manifest
4. Kubernetes Secret template

All manifests must be compatible with **FluxCD v2**.
