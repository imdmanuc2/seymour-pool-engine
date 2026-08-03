# Native Statistics Engine

**Document:** 12-NATIVE-STATISTICS.md

**Version:** 1.0 (Development)

---

# Purpose

The Native Statistics Engine provides real-time operational metrics directly from Seymour Pool Engine.

Unlike traditional mining platforms that rely on external dashboards or mining software to calculate performance, Seymour generates its own statistics directly from validated mining activity.

This allows every subsystem of the Seymour Platform to use a single, authoritative source of mining data.

---

# Design Goals

The Native Statistics Engine is designed to provide:

- Real-time pool statistics
- Real-time worker statistics
- Historical performance
- Low-latency API responses
- Accurate hashrate estimation
- Native integration with Nexus Command Center
- Long-term operational reporting

---

# Architecture

```
ASIC Miners

        │

Accepted Shares

        │

Share Validation

        │

Statistics Repository

        │

Statistics Service

        │

REST API

        │

Nexus Command Center
```

Every accepted share contributes directly to platform statistics.

---

# Data Sources

Statistics are generated from:

- Active Stratum sessions
- Validated share submissions
- Variable Difficulty
- Mining jobs
- Worker activity

No third-party mining software is required.

---

# Core Metrics

The engine tracks:

- Active workers
- Active pools
- Pool hashrate
- Worker hashrate
- Accepted shares
- Rejected shares
- Total shares
- Efficiency
- Rejection rate
- Last accepted share
- Last submitted share

---

# Pool Statistics

Pool statistics summarize the entire mining operation.

Example metrics include:

```
Pool Hashrate

Active Workers

Accepted Shares

Rejected Shares

Efficiency
```

Pool statistics are available through:

```
/api/v1/statistics/overview
```

---

# Worker Statistics

Each worker maintains independent statistics.

Metrics include:

- Worker name
- Current difficulty
- Current hashrate
- Share totals
- Online status
- Last activity
- Last accepted share
- Connection state

Worker statistics are available through:

```
/api/v1/statistics/workers
```

---

# Worker Detail

Detailed worker information is available through:

```
/api/v1/statistics/workers/{worker}
```

This endpoint provides information for a single mining worker.

---

# Engine Statistics

Engine statistics describe Seymour itself rather than mining performance.

Examples include:

- Share processing rate
- Active sessions
- Submission rate
- Engine activity

Available through:

```
/api/v1/statistics/engine
```

---

# Time Windows

Statistics may be calculated across multiple windows.

Supported examples include:

```
1 minute

5 minutes

15 minutes

1 hour
```

Additional windows may be added in future releases.

---

# Hashrate Calculation

Hashrate is estimated from accepted shares.

The calculation considers:

- Share difficulty
- Accepted shares
- Time window

Because calculations are based on validated work, hashrate reflects actual mining activity rather than reported hardware estimates.

---

# Efficiency

Efficiency measures accepted work relative to total submissions.

Conceptually:

```
Accepted Shares

÷

Total Shares
```

Healthy workers should maintain a high efficiency value.

---

# Rejection Rate

The rejection rate measures invalid submissions.

Conceptually:

```
Rejected Shares

÷

Total Shares
```

High rejection rates may indicate:

- Network latency
- Incorrect difficulty
- Miner configuration issues
- Protocol incompatibilities

---

# Active Workers

Workers are considered active when:

- Connected
- Authorized
- Submitting shares
- Not disconnected

Inactive workers remain available for historical reporting.

---

# Historical Statistics

Statistics remain available after miners disconnect.

Historical information supports:

- Trend analysis
- Capacity planning
- Diagnostics
- Operational reporting

---

# Database Storage

Statistics are periodically persisted within:

```
native_statistics_snapshots
```

Stored values may include:

- Timestamp
- Pool hashrate
- Worker count
- Accepted shares
- Rejected shares
- Efficiency

Snapshots reduce expensive real-time calculations.

---

# REST API Integration

Statistics are exposed through the REST API.

Primary endpoints include:

```
/statistics/overview

/statistics/workers

/statistics/workers/{worker}

/statistics/engine
```

These endpoints provide the primary interface used by dashboards.

---

# Nexus Command Center

Nexus consumes the Native Statistics API to display:

- Pool dashboards
- Worker status
- Infrastructure Explorer
- CMDB assets
- Fleet health
- Operational dashboards
- Historical trends
- Alerting

The Statistics Engine is the authoritative source of mining performance within the Seymour Platform.

---

# Operational Benefits

Native statistics provide:

- Consistent reporting
- Low-latency dashboards
- Historical visibility
- Reduced external dependencies
- Unified platform metrics

---

# Future Enhancements

Future releases may include:

- WebSocket streaming
- Live time-series charts
- Per-device telemetry
- Pool comparison
- Predictive hashrate analysis
- Long-term trend analytics
- Export to external monitoring platforms

---

# Relationship to Other Components

The Native Statistics Engine depends on:

- Share Validation
- Stratum Sessions
- Variable Difficulty
- PostgreSQL

It supplies data to:

- REST API
- Nexus Command Center
- CMDB
- Alerting
- Reporting
- Automation

---

# Summary

The Native Statistics Engine transforms validated mining activity into actionable operational information.

It provides the Seymour Platform with a unified, database-backed source of mining intelligence that supports real-time monitoring, historical reporting, and future automation.

---

# Next Step

Continue with:

**13-NEXUS-COMMAND-CENTER-INTEGRATION.md**
