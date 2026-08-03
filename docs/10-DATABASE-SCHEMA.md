# Database Schema

**Document:** 10-DATABASE-SCHEMA.md

**Version:** 1.0 (Development)

---

# Purpose

Seymour Pool Engine is built around a PostgreSQL database.

Unlike many mining pools that keep large portions of their state in memory, Seymour persists operational information to the database, allowing the platform to recover cleanly from restarts, provide historical analytics, and integrate with external systems such as Nexus Command Center.

This document describes the core database objects that support the Stratum engine.

---

# Design Goals

The database is designed to provide:

- Persistent mining sessions
- Historical reporting
- Complete audit history
- Native statistics
- High-performance queries
- CMDB integration
- Operational diagnostics
- Future horizontal scalability

---

# Schema

All Seymour application tables reside within:

```
seymour_engine
```

Example:

```
seymour_engine.stratum_sessions
```

---

# Core Tables

The primary operational tables are:

```
schema_migrations

stratum_sessions

stratum_jobs

stratum_submissions

stratum_difficulty_history

native_statistics_snapshots
```

Additional tables may be introduced as Version 1.0 evolves.

---

# schema_migrations

Tracks every database migration applied to the system.

Purpose:

- Installation verification
- Upgrade management
- Package validation

Typical fields include:

- Migration ID
- Applied timestamp

---

# stratum_sessions

Stores every miner connection.

Each record represents one Stratum session.

Typical information:

- Session ID
- Worker name
- Remote IP
- Remote port
- Connected time
- Last activity
- Last share
- Difficulty
- Accepted shares
- Total submissions
- Disconnect time

A worker may have many historical sessions.

---

# stratum_jobs

Stores mining jobs issued by Seymour.

Typical fields include:

- Job ID
- Block height
- Previous block hash
- Coinbase data
- Merkle branches
- Version
- nBits
- nTime
- Source
- Active flag

Jobs remain available for later share validation.

---

# stratum_submissions

Records every submitted share.

Typical fields include:

- Submission ID
- Session ID
- Worker name
- Job ID
- Extranonce2
- nTime
- Nonce
- Accepted
- Reject reason
- Share difficulty
- Block candidate
- Header
- Timestamp

This table forms the primary historical record of mining activity.

---

# stratum_difficulty_history

Stores every Variable Difficulty adjustment.

Typical fields include:

- Worker
- Old difficulty
- New difficulty
- Observed share interval
- Target share interval
- Reason
- Timestamp

This table supports diagnostics and performance analysis.

---

# native_statistics_snapshots

Stores periodic statistical snapshots.

Examples include:

- Pool hashrate
- Worker hashrate
- Active workers
- Accepted shares
- Rejected shares
- Efficiency

Snapshots power the Statistics API without requiring expensive live aggregation.

---

# Relationships

```
Stratum Session
        │
        │
        ▼
Submitted Shares
        │
        ▼
Mining Job
        │
        ▼
Difficulty History
        │
        ▼
Statistics
```

---

# Session Lifecycle

```
Connect

↓

Authorize

↓

Mine

↓

Submit Shares

↓

Disconnect
```

Every stage is recorded in PostgreSQL.

---

# Job Lifecycle

```
Bitcoin Template

↓

Create Job

↓

Store Job

↓

Issue Job

↓

Validate Shares

↓

Expire Job
```

---

# Share Lifecycle

```
Receive Share

↓

Validate

↓

Accept / Reject

↓

Store

↓

Statistics

↓

Historical Reporting
```

---

# Indexing Strategy

The database uses indexes to support fast operational queries.

Examples include indexes on:

- Session ID
- Worker name
- Job ID
- Created timestamp
- Accepted status

Indexes are optimized for:

- Live dashboards
- Historical reporting
- Statistics
- API queries

---

# Historical Data

Historical mining data is intentionally retained.

Benefits include:

- Long-term hashrate analysis
- Worker history
- Performance tuning
- Troubleshooting
- Capacity planning

Future releases may introduce configurable retention policies.

---

# Native Statistics

Rather than calculating every statistic from raw submissions, Seymour periodically creates summarized statistics.

Benefits include:

- Faster API responses
- Lower database load
- Consistent reporting
- Improved dashboard performance

---

# CMDB Integration

The database provides operational data to Nexus Command Center.

Examples include:

- Active miners
- Pool status
- Worker performance
- Hashrate
- Difficulty
- Session health
- Historical activity

Nexus consumes this information to build the infrastructure digital twin.

---

# Recovery

Because operational state is persisted, Seymour can recover from process restarts without losing historical mining information.

Database persistence improves:

- Reliability
- Auditing
- Diagnostics
- Operational continuity

---

# Scalability

The schema is designed to support:

- Thousands of workers
- Millions of shares
- Continuous statistics
- Long-term history

Additional partitioning and archival strategies may be introduced in future versions.

---

# Relationship to Other Components

The database supports:

- Stratum Engine
- Job Engine
- Variable Difficulty
- Share Validation
- Native Statistics
- REST API
- Nexus Command Center

Every major subsystem depends upon the database.

---

# Next Step

Continue with:

**11-REST-API.md**
