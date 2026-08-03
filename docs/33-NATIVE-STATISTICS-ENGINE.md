# Native Statistics Engine

**Document:** 33-NATIVE-STATISTICS-ENGINE.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document describes the internal architecture of the Seymour Pool Engine Native Statistics Engine.

The Native Statistics Engine is responsible for transforming validated mining activity into real-time operational metrics without relying on third-party mining software.

It is the authoritative source for all mining telemetry consumed by the REST API and Nexus Command Center.

---

# Design Goals

The Native Statistics Engine is designed to provide:

- Accurate real-time telemetry
- Low-latency calculations
- Database-backed persistence
- Worker-level metrics
- Pool-level metrics
- API-ready responses
- Historical extensibility

---

# Philosophy

Statistics should be derived from validated mining activity.

The engine does not estimate activity from network traffic or miner-reported values.

Instead, statistics originate from accepted share submissions recorded by Seymour itself.

```
Validated Share

↓

Persistent Storage

↓

Statistics Engine

↓

REST API

↓

Nexus Command Center
```

---

# Source of Truth

The Native Statistics Engine consumes data from:

- Accepted shares
- Worker sessions
- Difficulty history
- Job history

It does not depend on external mining software.

---

# Processing Pipeline

```
Share Accepted

↓

Persist Submission

↓

Statistics Repository

↓

Statistics Service

↓

REST API

↓

Client
```

---

# Statistics Levels

The engine currently produces statistics for:

- Individual workers
- Entire pool
- Active sessions

Future versions may add:

- Device groups
- Multiple pools
- Historical trends
- Fleet summaries

---

# Worker Metrics

Typical worker metrics include:

- Current hashrate
- Accepted shares
- Rejected shares
- Share efficiency
- Assigned difficulty
- Online status
- Last activity
- Session duration

---

# Pool Metrics

Pool metrics include:

- Total hashrate
- Active workers
- Accepted shares
- Rejected shares
- Efficiency
- Last accepted share
- Last submitted share

---

# Time Windows

Version 1.0 supports configurable calculation windows.

Typical windows include:

```
1 minute

5 minutes

15 minutes

1 hour
```

Longer windows reduce variance while shorter windows provide immediate operational visibility.

---

# Hashrate Calculation

Hashrate is estimated using accepted shares and assigned difficulty within the selected time window.

The calculation is deterministic and repeatable.

Rejected shares do not contribute to estimated hashrate.

---

# Worker Activity

A worker is considered active when:

- A Stratum session exists
- Recent mining activity is present
- Shares are being accepted within the configured window

Historical sessions remain available but do not contribute to active worker counts.

---

# Efficiency

Efficiency is calculated as:

```
Accepted Shares

──────────────

Total Shares
```

Future versions may incorporate additional quality metrics.

---

# Repository Layer

The Statistics Repository is responsible for:

- SQL queries
- Aggregation
- Filtering
- Window calculations
- Database optimization

Business logic remains in the service layer.

---

# Service Layer

The Statistics Service:

- Validates requests
- Selects calculation windows
- Performs calculations
- Formats responses
- Supplies REST API objects

---

# REST API Integration

Native Statistics powers:

```
/statistics/overview

/statistics/workers

/statistics/engine
```

These endpoints expose calculated telemetry without revealing database implementation details.

---

# Nexus Integration

Nexus consumes Native Statistics to populate:

- Home Dashboard
- CMDB
- Infrastructure Explorer
- Operations Center
- Digital Twin
- Recommendations
- AI Context

Seymour remains the authoritative operational source.

---

# Performance

Statistics queries are optimized through:

- Indexed tables
- Time-window filtering
- Aggregate SQL
- Minimal application-side processing

Future releases may introduce caching where appropriate.

---

# Historical Expansion

The architecture is designed to support future capabilities such as:

- Hourly summaries
- Daily summaries
- Historical charts
- Trend analysis
- Capacity planning

These features can be added without redesigning the existing calculation pipeline.

---

# Failure Handling

If statistics cannot be calculated:

- Return meaningful API errors
- Preserve Stratum operation
- Continue recording shares
- Log calculation failures

Mining should continue even if statistics are temporarily unavailable.

---

# Design Principles

The Native Statistics Engine follows these principles:

- Seymour owns mining truth.
- Statistics originate from validated shares.
- Operational metrics are deterministic.
- REST APIs expose calculated data, not raw database structures.
- External systems consume statistics rather than calculating their own.

---

# Future Enhancements

Potential improvements include:

- Long-term trend analysis
- Historical retention policies
- Predictive analytics
- Prometheus exporters
- Streaming telemetry
- AI-assisted operational insights

---

# Summary

The Native Statistics Engine transforms validated mining activity into authoritative operational telemetry.

It provides the foundation for Seymour's REST API, Nexus Command Center integration, and future analytics while remaining independent of external mining software.

---

# Next Step

Continue with:

**34-VARDIFF-ENGINE.md**
