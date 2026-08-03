# Stratum Internals

**Document:** 32-STRATUM-INTERNALS.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document describes the internal architecture of the Seymour Pool Engine Stratum server.

Unlike the user documentation, this specification is intended for developers extending or maintaining the Stratum implementation.

---

# Design Goals

The Stratum server is designed to provide:

- High throughput
- Low latency
- Deterministic validation
- Session isolation
- Production stability
- Detailed operational telemetry

Every design decision should preserve these goals.

---

# High-Level Architecture

```
TCP Listener

↓

Connection Handler

↓

Session Manager

↓

JSON-RPC Decoder

↓

Dispatcher

↓

Share Validator

↓

Statistics

↓

Database

↓

Bitcoin RPC
```

Each stage has a single responsibility.

---

# Primary Components

The Stratum subsystem consists of:

- TCP Server
- Connection Manager
- Session Manager
- JSON-RPC Codec
- Dispatcher
- Job Manager
- Share Validator
- VarDiff Controller
- Block Submission Service
- Repository Layer

---

# Connection Lifecycle

```
TCP Connect

↓

Session Created

↓

Subscribe

↓

Difficulty Assigned

↓

Job Issued

↓

Authorize

↓

Mining

↓

Submit Shares

↓

Disconnect

↓

Session Archived
```

---

# Session Model

Each active miner owns exactly one Stratum session.

A session maintains:

- Session ID
- Worker Name
- Authorization State
- Extranonce1
- Extranonce2 Size
- Current Difficulty
- Issued Jobs
- Share Counters
- Activity Timestamps
- Version Rolling State

Sessions must never share mutable mining state.

---

# Job Lifecycle

Jobs are created from Bitcoin block templates.

```
Bitcoin Template

↓

Internal Job

↓

Persisted

↓

Assigned to Session

↓

Mining.notify

↓

Share Validation

↓

Expired
```

Jobs remain available long enough to validate delayed submissions.

---

# Dispatcher

The dispatcher processes all incoming JSON-RPC methods.

Current supported methods include:

- mining.subscribe
- mining.authorize
- mining.submit

Future protocol extensions should be implemented within the dispatcher while preserving protocol compatibility.

---

# Job Ownership

Jobs are issued to individual sessions.

Each session maintains a bounded collection of recently issued job identifiers and their assigned difficulty.

Incoming shares are validated only against jobs issued to that session.

This prevents stale or foreign jobs from being accepted.

---

# Share Validation Pipeline

```
Submit

↓

Lookup Session

↓

Lookup Job

↓

Verify Ownership

↓

Verify Difficulty

↓

Build Header

↓

Double SHA256

↓

Calculate Difficulty

↓

Accept / Reject
```

Only validated shares proceed to persistence.

---

# Variable Difficulty

VarDiff continuously monitors worker performance.

When an adjustment is required:

```
Calculate Difficulty

↓

Update Session

↓

Issue mining.set_difficulty

↓

Generate New Job

↓

Issue mining.notify
```

Existing jobs retain their originally assigned difficulty.

---

# Session Isolation

Workers must never affect each other's mining state.

Isolation includes:

- Job tracking
- Difficulty
- Statistics
- Authorization
- Extranonce allocation

---

# Extranonce Management

Each session receives a unique Extranonce1 value.

Miners generate Extranonce2 locally.

Together they guarantee unique coinbase construction.

---

# Version Rolling

When negotiated:

- Supported mask stored in session
- Submitted bits validated
- Invalid bits rejected

Version rolling validation occurs before share acceptance.

---

# Persistence

Operational state is persisted through the repository layer.

Typical objects include:

- Sessions
- Jobs
- Shares
- Difficulty history
- Statistics

Business logic should remain outside SQL operations.

---

# Logging

Important events include:

- Connection opened
- Connection closed
- Subscribe
- Authorize
- Job issued
- Difficulty change
- Share accepted
- Share rejected
- Block candidate

Logs should support production diagnostics without excessive verbosity.

---

# Error Handling

Malformed requests should:

- Reject only the offending request
- Preserve the session where possible
- Produce meaningful log entries
- Avoid affecting unrelated workers

Unexpected exceptions should never terminate the Stratum server.

---

# Performance

The Stratum server should prioritize:

- Low allocation rates
- Predictable latency
- Efficient validation
- Minimal database contention

Performance optimizations must not compromise correctness.

---

# Thread Safety

Shared state should be minimized.

Session state should remain isolated to the owning connection wherever possible.

Shared repositories and caches must be thread-safe.

---

# Future Evolution

Future enhancements may include:

- Additional Stratum extensions
- TLS transport
- Multi-threaded validation
- Cluster-aware session routing
- Horizontal scaling

These enhancements should preserve protocol compatibility.

---

# Summary

The Seymour Stratum implementation is built around isolated session state, deterministic share validation, and production-grade operational visibility.

Future development should extend the implementation while preserving these architectural principles.

---

# Next Step

Continue with:

**33-NATIVE-STATISTICS-ENGINE.md**
