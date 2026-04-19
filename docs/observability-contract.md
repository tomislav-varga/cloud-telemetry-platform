# Observability Contract (Dev)

This document defines the observability baseline for the Prometheus and Grafana rollout in the dev environment.

## Goals

- Detect service outages quickly.
- Detect elevated API error rates.
- Detect telemetry ingestion slowdowns.
- Detect edge device transmission gaps.
- Keep metric label cardinality bounded.

## Scope

- Environment: dev Kubernetes cluster.
- Stack: kube-prometheus-stack (Prometheus Operator + Grafana + Alertmanager).
- Metrics sources: backend API, edge service, Flux controllers, PostgreSQL exporter.

## Naming and Label Rules

- Prefix backend metrics with `telemetry_api_`.
- Prefix edge metrics with `edge_`.
- Use base units in metric names (for example, `_seconds`, `_bytes`, `_total`).
- Use only bounded labels. Allowed high-level labels:
  - `method`
  - `path`
  - `status_code`
  - `result`
  - `reason` (from a fixed enum)
  - `device_id` (allowed only for edge gauges/counters; must be stable and finite in dev)
- Never use timestamps, request ids, or unbounded payload values as labels.

## Backend Metrics Contract

## Required

- `telemetry_api_requests_total{method,path}` (counter)
  - Total requests accepted by the API middleware.
- `telemetry_api_errors_total{method,path,status_code}` (counter)
  - Total HTTP responses with status >= 400.
- `telemetry_api_request_duration_seconds{method,path,status_code}` (histogram)
  - End-to-end request latency recorded in middleware.
- `telemetry_records_ingested_total` (counter)
  - Successful ingest events.
- `authentication_failures_total{reason}` (counter)
  - Failed auth attempts by fixed reason enum.
- `authenticated_requests_total` (counter)
  - Successful auth checks.

## Optional (Phase 2+)

- `telemetry_api_auth_duration_seconds{result}` (histogram)
- `telemetry_api_db_query_duration_seconds{operation}` (histogram)

## Edge Metrics Contract

## Required

- `edge_sensor_read_total{device_id,result}` (counter)
  - `result` enum: `success|failure`.
- `edge_sensor_read_duration_seconds{device_id,result}` (histogram)
- `edge_transmission_total{device_id,result}` (counter)
  - `result` enum: `success|failure`.
- `edge_transmission_duration_seconds{device_id,result}` (histogram)
- `edge_transmission_retries_total{device_id,reason}` (counter)
  - `reason` enum: `timeout|connection_error|server_error`.
- `edge_temperature_celsius{device_id}` (gauge)
- `edge_humidity_percent{device_id}` (gauge)
- `edge_last_success_unixtime{device_id}` (gauge)

## Alert Baseline (Dev)

These alerts are intentionally conservative for dev and can be tightened later.

1. Backend down
- Expr: `up{job="backend"} == 0`
- For: `2m`
- Severity: `critical`

2. High backend error rate
- Expr: `sum(rate(telemetry_api_errors_total[5m])) / sum(rate(telemetry_api_requests_total[5m])) > 0.05`
- For: `10m`
- Severity: `warning`

3. High backend p95 latency
- Expr: `histogram_quantile(0.95, sum by (le) (rate(telemetry_api_request_duration_seconds_bucket[5m]))) > 1.0`
- For: `10m`
- Severity: `warning`

4. Scrape target down
- Expr: `up == 0`
- For: `10m`
- Severity: `warning`

5. Edge not transmitting
- Expr: `time() - edge_last_success_unixtime > 600`
- For: `10m`
- Severity: `critical`

6. Edge temperature too low
- Expr: `edge_temperature_celsius{environment="dev",source="edge"} < 21`
- For: `2m`
- Severity: `warning`

7. Edge temperature too high
- Expr: `edge_temperature_celsius{environment="dev",source="edge"} > 23`
- For: `2m`
- Severity: `warning`

## Dashboard Minimums

1. API RED panel group
- Request rate
- Error rate
- p50/p95 latency

2. Ingestion panel group
- Ingested records per minute
- Auth failure rate

3. Edge panel group
- Latest temperature/humidity per device
- Transmission success vs failure
- Last success age

4. Platform panel group
- Flux controller health
- PostgreSQL exporter health

## Acceptance Criteria for Phase 1

- Contract file exists and is reviewed.
- Metric names and labels are agreed and stable.
- Alert threshold defaults are documented.
- Follow-up implementation phases reference this contract.
