# Seymour Pool Engine Architecture

**Version:** 1.0 (Development)

---

# Purpose

Seymour Pool Engine is a modern Bitcoin mining pool engine built to provide a production-quality Stratum server, native Bitcoin share validation, and a modular architecture suitable for long-term development and integration.

Rather than adapting decades-old mining software, Seymour is designed around modern software engineering principles including modular services, deterministic validation, comprehensive testing, PostgreSQL persistence, and REST-based observability.

The engine is intended to operate both as a standalone mining pool and as the mining backend for Nexus Command Center.

---

# Architectural Goals

Version 1.0 focuses on delivering a complete, production-ready mining workflow.

Primary goals include:

- Native Stratum implementation
- Native Bitcoin job generation
- Native share validation
- Variable Difficulty (VarDiff)
- Native statistics engine
- PostgreSQL persistence
- REST API
- Operational observability
- Nexus Command Center integration

---

# System Architecture

```
                         Bitcoin Core
                              │
                              │ RPC
                              ▼
                   ┌─────────────────────┐
                   │ Block Template      │
                   │ Generation          │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Job Engine          │
                   └──────────┬──────────┘
                              │
                              ▼
 ASIC Miners ─────► Stratum Server ─────► Dispatcher
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
      VarDiff          Share Validation     Block Submission
          │                   │                    │
          └───────────────────┴────────────────────┘
                              │
                              ▼
                        PostgreSQL
                              │
                              ▼
                        Statistics
                              │
                              ▼
                          REST API
                              │
                              ▼
                   Nexus Command Center
```

---

# Major Components

## Stratum Server

The Stratum Server manages all miner communication.

Responsibilities include:

- TCP listener
- Session lifecycle
- Subscribe
- Authorize
- Notify
- Share submission
- Connection cleanup

The server intentionally contains very little mining logic.

Its primary responsibility is communication.

---

## Dispatcher

The Dispatcher is the heart of Seymour.

Nearly every mining operation flows through the dispatcher.

Responsibilities include:

- protocol processing
- job distribution
- share validation
- difficulty management
- share persistence
- block candidate detection
- notifications

The dispatcher coordinates the rest of the engine while avoiding ownership of persistent state.

---

## Job Engine

The Job Engine converts Bitcoin Core block templates into Stratum mining jobs.

Each generated job contains:

- Previous block hash
- Coinbase transaction
- Merkle branches
- Block version
- Network difficulty
- Timestamp
- Work identifier

Jobs are persisted so every submitted share can later be reconstructed exactly as it was originally issued.

---

## Share Validation

Every submitted share is independently reconstructed and validated.

Validation consists of:

1. Coinbase reconstruction
2. Merkle root calculation
3. Block header construction
4. Double SHA256 hashing
5. Share difficulty calculation
6. Share target comparison
7. Network target comparison

Validation is completely deterministic.

Given the stored job and miner submission, Seymour can always reproduce the validation result.

---

## Variable Difficulty (VarDiff)

Variable Difficulty automatically adjusts worker difficulty to maintain an approximately constant share submission interval.

When difficulty changes:

1. Worker difficulty is updated.
2. A new mining job is immediately generated.
3. The new job is permanently associated with that assigned difficulty.
4. Future submissions are validated against the difficulty assigned when the job was issued.

This eliminates incorrect rejections caused by miners submitting work generated under an older difficulty.

---

## Statistics Engine

The statistics engine calculates mining metrics directly from validated shares.

Metrics include:

- Pool hashrate
- Worker hashrate
- Accepted shares
- Rejected shares
- Efficiency
- Active workers
- Active pools
- Share rates

No external mining software is required to calculate these statistics.

---

## Database Layer

PostgreSQL is the authoritative data store.

Major persisted objects include:

- Sessions
- Workers
- Jobs
- Shares
- Difficulty history
- Statistics snapshots
- Schema migrations

The database is designed to provide both operational state and complete historical auditing.

---

## REST API

The REST API exposes engine state without participating in mining operations.

Current consumers include:

- Nexus Command Center
- Monitoring
- Automation
- Dashboards
- Operational tooling

The API is intentionally read-oriented and separate from the mining protocol.

---

# Internal Flow

A simplified mining workflow is:

```
Miner Connects
       │
       ▼
Subscribe
       │
Authorize
       │
Receive Job
       │
Mine
       │
Submit Share
       │
Validate Share
       │
Accepted?
       │
 ┌─────┴─────┐
 │           │
 ▼           ▼
Reject     Persist
                │
                ▼
      Update Statistics
                │
                ▼
       Adjust Difficulty
                │
                ▼
         Issue New Job
```

---

# Session Model

Each connected miner owns an independent session.

A session contains:

- Worker identity
- Extranonce
- Current difficulty
- Assigned job history
- Connection metadata
- Share statistics
- Authorization state

Sessions are isolated from one another.

No worker shares state with another connected miner.

---

# Persistence Model

Seymour persists operational state whenever practical.

Persisted objects include:

- Mining jobs
- Share submissions
- Difficulty changes
- Sessions
- Statistics

This provides complete traceability for diagnostics and historical analysis.

---

# Design Principles

The architecture follows several guiding principles.

## Modular

Each subsystem has a single responsibility.

---

## Deterministic

Every accepted share can be reproduced from stored data.

---

## Observable

Operational state should be inspectable without attaching a debugger.

---

## Testable

Core mining logic should be unit tested independently from networking.

---

## Production First

Engineering decisions prioritize correctness and maintainability over shortcuts.

---

## Native

Critical mining functionality is implemented directly within Seymour rather than delegated to external mining software.

---

# Integration with Nexus

Seymour and Nexus have distinct responsibilities.

## Seymour Owns

- Mining protocol
- Sessions
- Jobs
- Share validation
- Variable Difficulty
- Statistics
- Block candidates
- Database persistence

---

## Nexus Owns

- CMDB
- Asset inventory
- Infrastructure topology
- Operational workflows
- Automation
- Dashboards
- AI context
- Recommendations
- Alerting

Nexus consumes Seymour's operational data but does not perform mining.

---

# Version 1.0 Scope

Version 1.0 delivers a complete mining engine capable of:

- Accepting ASIC connections
- Generating Bitcoin jobs
- Validating shares
- Dynamically adjusting difficulty
- Recording mining history
- Calculating native statistics
- Exposing operational APIs
- Integrating with Nexus Command Center

Future releases will build upon this foundation with additional algorithms, distributed mining capabilities, clustering, enhanced automation, and expanded operational tooling.
