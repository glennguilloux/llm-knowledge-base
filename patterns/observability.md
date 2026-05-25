---
id: "patterns-observability"
title: "Observability Basics: Tracing, Metrics, Logging"
language: "multi"
category: "patterns"
subcategory: "operations"
tags: ["observability", "tracing", "metrics", "opentelemetry", "prometheus", "jaeger"]
version: ""
retrieval_hint: "Observability tracing metrics OpenTelemetry Prometheus Jaeger logging"
last_verified: "2026-05-24"
confidence: "high"
---

# Observability Basics: Tracing, Metrics, Logging

## When to Use
- Debugging distributed systems (microservices, event-driven)
- Performance monitoring and bottleneck identification
- Alerting on error rates, latency percentiles, saturation
- Understanding request flow across services

## Standard Pattern

```python
# --- OpenTelemetry tracing ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

provider = TracerProvider()
exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

async def process_order(order_id: int):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order_id", order_id)

        with tracer.start_as_current_span("validate_order"):
            await validate_order(order_id)

        with tracer.start_as_current_span("charge_payment"):
            await charge_payment(order_id)

        with tracer.start_as_current_span("send_confirmation"):
            await send_confirmation(order_id)
```

```python
# --- Prometheus metrics ---
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "endpoint"])
ACTIVE_CONNECTIONS = Gauge("active_connections", "Active connections")

# Record metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)

    return response

# Expose metrics endpoint
start_http_server(9090)  # Prometheus scrapes from here
```

```yaml
# --- Grafana dashboard queries ---
# Request rate: rate(http_requests_total[5m])
# P99 latency: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
# Error rate: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

## Common Mistakes

```text
# WRONG: Too many metric cardinality
REQUEST_COUNT.labels(method, path, user_id, ip).inc()
# user_id and ip create millions of unique series!

# CORRECT: Low-cardinality labels
REQUEST_COUNT.labels(method, path, status).inc()

# WRONG: Not sampling traces in production
# Tracing every request = massive storage and overhead

# CORRECT: Sample 1-10% of traces
sampler = TraceIdRatioBased(0.01)  # 1% sampling

# WRONG: Metrics endpoint not secured
# Anyone can scrape /metrics and see internal data

# CORRECT: Secure metrics endpoint
# Only allow Prometheus IP or use authentication
```

## Gotchas
- Three pillars: logs (events), metrics (numbers), traces (request flow)
- OpenTelemetry is the standard for instrumentation — vendor-neutral
- High-cardinality labels (user_id, request_id) explode metric storage
- Sample traces in production — 1-10% is typical
- Prometheus pulls metrics; Jaeger/Zipkin collect traces; ELK collects logs
- Use Grafana for dashboards, Alertmanager for alerts
- Correlation: trace ID in logs links logs to traces
- RED method: Rate, Errors, Duration for services; USE method: Utilization, Saturation, Errors for resources

## Related
- patterns/structured-logging.md
- patterns/health-checks.md
- python/infra/sentry-integration.md
