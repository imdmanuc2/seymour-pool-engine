# Stratum Engine

**Document:** 06-STRATUM-ENGINE.md

**Version:** 1.0 (Development)

---

# Purpose

The Seymour Stratum Engine is responsible for all communication between mining hardware and the Bitcoin network.

It accepts miner connections, distributes mining jobs, validates submitted shares, manages Variable Difficulty (VarDiff), records operational telemetry, and submits valid block candidates to Bitcoin Core.

Unlike traditional mining pools where Stratum is tightly coupled to payout logic, Seymour separates the mining protocol from pool management, making the Stratum engine reusable across solo, public, and future enterprise deployments.

---

# Responsibilities

The Stratum Engine is responsible for:

- Accepting TCP miner connections
- Managing mining sessions
- Authorizing workers
- Negotiating protocol extensions
- Issuing mining jobs
- Managing extranonce allocation
- Variable Difficulty (VarDiff)
- Share validation
- Duplicate detection
- Block candidate validation
- Native statistics generation
- Persistent session tracking
- Operational logging

---

# Architecture

```
             ASIC Miner
                  │
                  │ JSON-RPC
                  │
        ┌─────────▼─────────┐
        │  Stratum Server   │
        └─────────┬─────────┘
                  │
        Session Manager
                  │
        Job Dispatcher
                  │
      Share Validator
                  │
      Statistics Engine
                  │
      PostgreSQL Database
                  │
      Bitcoin Core RPC
```

---

# Connection Lifecycle

Every miner follows the same lifecycle.

```
TCP Connect

↓

mining.subscribe

↓

mining.authorize

↓

mining.set_difficulty

↓

mining.notify

↓

mining.submit

↓

Share Validation

↓

Accepted / Rejected

↓

Disconnect
```

Each step is independently logged and recorded.

---

# Session Management

Each miner receives a unique session.

Session information includes:

- Session ID
- Worker name
- Remote IP
- Remote port
- Extranonce1
- Extranonce2 size
- Current difficulty
- Connection time
- Last activity
- Share counters

Sessions remain active until:

- Miner disconnects
- Idle timeout
- Server shutdown

Historical sessions remain stored in PostgreSQL.

---

# Subscription

The first RPC request is:

```
mining.subscribe
```

The server responds with:

- Subscription identifiers
- Extranonce1
- Extranonce2 size

At this point the miner has not yet been authorized.

---

# Authorization

Next request:

```
mining.authorize
```

Worker names typically use:

```
wallet.worker
```

Example

```
bc1xxxxxxxxxxxxx.001
```

Authorization records:

- Worker name
- Session
- Timestamp

Authorization immediately triggers job generation.

---

# Job Generation

Jobs originate from current Bitcoin block templates.

Each job contains:

- Job ID
- Previous block hash
- Coinbase Part 1
- Coinbase Part 2
- Merkle branches
- Block version
- nBits
- nTime
- Clean Jobs flag

Jobs are persisted before being transmitted.

---

# Job Distribution

Jobs are transmitted using:

```
mining.notify
```

Each worker receives jobs independently.

Variable Difficulty may cause different workers to receive different jobs.

---

# Extranonce Management

Each session receives a unique Extranonce1.

Example

```
6d593857
```

ASIC firmware generates Extranonce2 locally.

Coinbase construction:

```
coinbase1

+

extranonce1

+

extranonce2

+

coinbase2
```

The completed coinbase is hashed to construct the Merkle root.

---

# Variable Difficulty

Variable Difficulty (VarDiff) adjusts worker difficulty to achieve a target share interval.

Typical progression:

```
42

↓

84

↓

168

↓

336

↓

672

↓

1344

↓

2688

↓

5376
```

Each adjustment generates:

- mining.set_difficulty
- New mining job

Both are issued together to prevent protocol races.

---

# Session-Based Job Tracking

Each mining job is associated with the difficulty active when it was created.

The session stores:

```
job_id

↓

assigned difficulty
```

When a share arrives:

```
submitted job

↓

lookup assigned difficulty

↓

validate using original difficulty
```

This prevents historical jobs from being evaluated using newer difficulties.

This mechanism eliminated nearly all false "low difficulty share" rejections during VarDiff transitions.

---

# Share Validation

For every submitted share Seymour:

1. Validates parameters
2. Builds coinbase
3. Calculates Merkle root
4. Builds block header
5. Double SHA256 hash
6. Calculates achieved difficulty
7. Compares against share target
8. Compares against network target

Results:

```
Accepted

Rejected

Block Candidate
```

---

# Duplicate Detection

Every submission receives a fingerprint.

Duplicate submissions are rejected before validation.

This protects against:

- Miner retransmission
- Network retries
- Duplicate shares

---

# Block Candidate Validation

If a share exceeds network difficulty:

```
Share

↓

Block Candidate

↓

Bitcoin Core RPC

↓

submitblock
```

Bitcoin Core determines final acceptance.

---

# Native Statistics

The Stratum engine continuously generates statistics.

Metrics include:

- Pool hashrate
- Worker hashrate
- Accepted shares
- Rejected shares
- Efficiency
- Active workers
- Last share
- Last accepted share

Statistics power:

- REST API
- Future WebSocket feeds
- Nexus Command Center
- CMDB integration

---

# Database Tables

Primary tables include:

```
stratum_sessions

stratum_jobs

stratum_submissions

stratum_difficulty_history

native_statistics_snapshots
```

These tables provide the historical record of mining activity.

---

# Logging

Major events are logged.

Examples:

```
connection opened

authorized

JOB

VARDIFF_JOB

block candidate

connection closed
```

Logs are intended for operational diagnostics and troubleshooting.

---

# Current Protocol Support

Implemented:

- Stratum V1
- Variable Difficulty
- Version Rolling
- Session tracking
- Duplicate detection
- Native statistics

Planned:

- Extended telemetry
- WebSocket event streaming
- Multi-algorithm support
- Additional protocol compatibility improvements

---

# Relationship to Other Components

The Stratum Engine depends on:

- Bitcoin Core
- PostgreSQL
- Native Statistics
- Job Engine
- Block Submission Service

It provides data to:

- REST API
- Nexus Command Center
- CMDB
- Monitoring
- Alerting

---

# Design Goals

The Seymour Stratum Engine is designed to be:

- Deterministic
- Recoverable
- Observable
- Protocol compliant
- Database-backed
- Horizontally scalable
- Suitable for enterprise mining infrastructure

---

# Next Step

Continue with:

**07-SHARE-VALIDATION.md**
