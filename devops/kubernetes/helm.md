---
id: "devops-kubernetes-helm"
title: "Helm Charts"
language: "yaml"
category: "devops"
subcategory: "package-manager"
tags: ["helm", "chart", "template", "values", "release"]
version: "3.0+"
retrieval_hint: "Helm chart template values release package"
last_verified: "2026-05-22"
confidence: "high"
---

# Helm Charts

## When to Use
- Packaging Kubernetes applications
- Template-based deployments
- Environment-specific configuration
- Release management

## Standard Pattern

```yaml
# Chart.yaml
apiVersion: v2
name: my-app
description: My application Helm chart
version: 1.0.0
appVersion: "1.0.0"

---
# values.yaml
replicaCount: 3
image:
  repository: my-app
  tag: "1.0.0"
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 80
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"

---
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "my-app.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "my-app.name" . }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.port }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}

---
# templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "my-app.fullname" . }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.port }}
  selector:
    app: {{ include "my-app.name" . }}
```

## Usage

```bash
# Install
helm install my-release ./my-app

# Install with custom values
helm install my-release ./my-app --set replicaCount=5

# Upgrade
helm upgrade my-release ./my-app --set image.tag=2.0.0

# Rollback
helm rollback my-release 1

# Uninstall
helm uninstall my-release
```

## Common Mistakes

```yaml
# WRONG: Hardcoding values in templates
containers:
  - name: app
    image: my-app:1.0.0  # Hardcoded!

# CORRECT: Use values
containers:
  - name: app
    image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

```yaml
# WRONG: Using latest tag (non-reproducible deployments)
image:
  repository: my-app
  tag: latest

# CORRECT: Pin to specific version
image:
  repository: my-app
  tag: "1.0.0"
```

```yaml
# WRONG: Not setting resource limits (can cause OOM kills)
containers:
  - name: app
    resources: {}

# CORRECT: Set requests and limits
containers:
  - name: app
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "500m"
```

## Gotchas
- `values.yaml` provides defaults; override with `--set` or `-f custom-values.yaml`
- Use `include` for reusable template functions
- `toYaml` converts values to YAML
- `nindent` adds indentation
- Use `helm template` to render locally without installing
- Charts are versioned independently of app version

## Related
- devops/kubernetes/basics.md
- devops/docker/dockerfile-patterns.md
