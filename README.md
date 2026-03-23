# cloud-telemetry-platform

## Short Project Description

Cloud Telemetry Platform is an end-to-end room climate monitoring project.
An edge service on Raspberry Pi reads a DHT22 sensor, sends authenticated telemetry to a FastAPI backend, stores data in PostgreSQL, and exposes metrics for Prometheus and Grafana.
The platform is deployed in Kubernetes with a GitOps workflow and secure private networking.

## Motivation

I wanted to work on a project that solves a real problem. An area of a wall in my bedroom showed signs of mold, and I had to call a painter. He told me this usually happens when the temperature stays below 21 degrees Celsius for long periods. That sparked this project idea: monitor room temperature and humidity, and trigger alerts if the temperature drops below 21 degrees Celsius. I decided to build an end-to-end monitoring solution using a DHT22 sensor on my Raspberry Pi, with the backend and monitoring stack running in my Kubernetes cluster, plus visualization and alerting through Grafana and Prometheus.

## Headline Features

1. Async telemetry ingestion API with PostgreSQL (PR #1): FastAPI endpoints ingest, validate, and query sensor data with Alembic-managed schema and Prometheus-ready backend metrics.
2. Secure device API key authentication (PR #3): each edge device authenticates via X-API-Key using prefix lookup and bcrypt hash verification, with per-device usage tracking.
3. Clean-architecture edge runtime with resilient delivery (PR #2, PR #11): the edge service separates domain and infrastructure concerns, retries sensor/network failures, and runs as a hardened least-privilege systemd service.
4. GitOps deployment pipeline for app and database lifecycle (PR #4, PR #5, PR #10): Flux-managed layering coordinates PostgreSQL, migrations, and backend rollout with consistent runtime images.
5. Secure platform connectivity and secret handling (PR #6, PR #8): edge-to-backend traffic uses private Tailscale HTTPS ingress while cluster credentials are stored as SealedSecrets.
6. Full observability baseline with dashboards and alerts (PR #7, PR #9): Prometheus and Grafana provide RED metrics, edge health visibility, and alert-rule foundations for fast troubleshooting.

## System Architecture (ASCII)

+-----------------------+              +-------------------------------+
| Edge Device           | HTTPS + Key | Kubernetes Cluster (GitOps)   |
| Raspberry Pi + DHT22  +-------------> Backend API (FastAPI)         |
| edge service + retries|              | telemetry endpoints + metrics |
+-----------+-----------+              +---------------+---------------+
            |                                              |
            | /metrics                                     | SQL
            v                                              v
   +-------------------+                          +----------------------+
   | Prometheus Scrape |<-------------------------+ PostgreSQL           |
   | edge + backend    |                          | telemetry + devices  |
   +---------+---------+                          +----------+-----------+
             |                                                
             v                                                
      +-------------+        alerts/rules         +---------------------+
      | Grafana     |<----------------------------+ Prometheus Rules     |
      | dashboards  |                             | and Alertmanager cfg |
      +-------------+                             +---------------------+

## Video Demo

[![Cloud Telemetry Platform Demo](https://img.youtube.com/vi/ghD60_KQD9M/0.jpg)](https://www.youtube.com/watch?v=ghD60_KQD9M)