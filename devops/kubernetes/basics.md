---
id: "devops-kubernetes-basics"
title: "Kubernetes Basics"
language: "yaml"
category: "devops"
subcategory: "orchestration"
tags: ["kubernetes", "k8s", "pod", "deployment", "service", "ingress"]
version: "n/a"
retrieval_hint: "Kubernetes pod deployment service ingress manifest"
last_verified: "2026-05-22"
confidence: "high"
---

# Kubernetes Basics

## When to Use
- Container orchestration
- Scaling applications
- Service discovery
- Rolling deployments

## Standard Pattern

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
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
          image: my-app:1.0.0
          ports:
            - containerPort: 3000
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

## Common Mistakes

```yaml
# WRONG: No resource limits
containers:
  - name: app
    image: my-app:latest  # Can consume unlimited resources!

# CORRECT: Set resource limits
containers:
  - name: app
    image: my-app:1.0.0
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "500m"

# WRONG: Using 'latest' tag
image: my-app:latest  # Unpredictable deployments!

# CORRECT: Pin version
image: my-app:1.0.0
```

## Gotchas
- Always set resource requests and limits
- Use liveness and readiness probes
- Never use `latest` tag — pin versions
- `ClusterIP` is default service type (internal only)
- Use `Ingress` for external access
- `replicas` controls number of pod copies
- Use `kubectl apply -f` to create/update resources

## Related
- devops/kubernetes/helm.md
- devops/docker/dockerfile-patterns.md
