# REST API Reference

**Document:** 19-REST-API-REFERENCE.md

**Version:** 1.0 (Development)

---

# Purpose

This document describes the Version 1.0 REST API exposed by the Seymour Pool Engine.

The REST API provides operational access to mining telemetry, worker information, engine status, and health information while keeping Stratum communication separate from management and monitoring functions.

The API is intended for:

- Nexus Command Center
- Administrative dashboards
- Monitoring systems
- Automation
- Future SDKs
- Third-party integrations

---

# Base URL

Production example:

```
http://server:8561/api/v1/
```

Development example:

```
http://127.0.0.1:8561/api/v1/
```

---

# API Versioning

Version 1.0 uses:

```
/api/v1/
```

Future releases will introduce new API versions without breaking existing clients whenever practical.

---

# Content Type

Requests

```
application/json
```

Responses

```
application/json
```

---

# HTTP Status Codes

| Code | Meaning |
|-------|----------|
| 200 | Success |
| 201 | Created |
| 400 | Invalid Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 500 | Internal Server Error |

---

# Health Endpoint

## GET

```
/health
```

Purpose

Returns engine health.

Example

```bash
curl http://127.0.0.1:8561/api/v1/health
```

Example Response

```json
{
  "status":"healthy"
}
```

---

# Pool Statistics

## GET

```
/statistics/overview
```

Parameters

```
window
```

Supported values

```
1m
5m
15m
1h
```

Example

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=5m"
```

Typical Response

```json
{
  "source":"seymour-native-stratum",
  "hashrate":14431090114560.0,
  "activeWorkers":2,
  "acceptedShares":523,
  "rejectedShares":0,
  "efficiency":1.0
}
```

---

# Worker Statistics

## GET

```
/statistics/workers
```

Parameters

```
window
```

Returns

- Worker list
- Hashrate
- Difficulty
- Share counts
- Activity
- Online state

Example

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/workers?window=5m"
```

---

# Individual Worker

## GET

```
/statistics/workers/{worker}
```

Purpose

Returns statistics for a single worker.

---

# Engine Statistics

## GET

```
/statistics/engine
```

Provides engine-level operational metrics.

Example

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/engine?window=5m"
```

---

# Response Format

All responses follow a consistent JSON structure.

Typical fields include:

```
source
window
calculatedAt
hashrate
acceptedShares
rejectedShares
efficiency
```

Worker responses additionally include:

```
workerName
sessionId
difficulty
online
phase
lastActivityAt
```

---

# Time Windows

Supported windows

```
1m
5m
15m
1h
```

Future releases may support:

```
6h
12h
24h
7d
30d
```

---

# Error Responses

Example

```json
{
  "error":"invalid window"
}
```

Clients should always validate HTTP status codes before parsing results.

---

# Authentication

Version 1.0 assumes deployment on trusted networks.

Future releases may add:

- API keys
- OAuth
- Mutual TLS
- Service accounts

---

# Rate Limiting

Version 1.0 does not enforce API rate limiting.

Future enterprise deployments may introduce configurable request limits.

---

# Nexus Integration

Nexus Command Center consumes the REST API for:

- Home dashboard
- CMDB
- Infrastructure Explorer
- Recommendations
- Alerts
- AI Context
- Operations
- Digital Twin views

The REST API is the supported integration point between Seymour and Nexus.

---

# Operational Recommendations

Applications should:

- Cache responses briefly.
- Prefer 15-minute statistics for dashboards.
- Treat worker online state as authoritative.
- Avoid polling excessively.

---

# Future Endpoints

Potential additions include:

- Pool management
- Worker management
- Configuration
- RPC diagnostics
- Prometheus metrics
- WebSocket telemetry
- Historical reporting
- AI analytics

These features are outside the Version 1.0 scope.

---

# API Stability

Version 1.0 endpoints are intended to remain backward compatible throughout the 1.x release series whenever practical.

Breaking changes should only occur in future major versions.

---

# Summary

The Seymour Pool Engine REST API provides a stable, versioned interface for accessing operational mining telemetry, worker information, engine status, and future management capabilities.

It serves as the primary integration layer between the Pool Engine and Nexus Command Center while remaining suitable for third-party dashboards and automation.

---

# Documentation Complete

This concludes the Version 1.0 documentation set.

Future documentation should expand these references as new capabilities are introduced while preserving compatibility with the Version 1.0 architecture.
