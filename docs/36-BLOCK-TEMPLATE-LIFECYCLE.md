# Block Template Lifecycle

**Document:** 36-BLOCK-TEMPLATE-LIFECYCLE.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document describes how Bitcoin block templates move through the Seymour Pool Engine.

It defines the complete lifecycle from requesting a template from Bitcoin Core to issuing mining jobs to connected workers.

---

# Design Goals

The Block Template subsystem is designed to provide:

- Continuous work generation
- Deterministic job creation
- Efficient template refresh
- Worker isolation
- Complete auditability
- Fast block propagation

---

# Overview

The lifecycle begins with Bitcoin Core and ends with Stratum job notifications.

```
Bitcoin Core

↓

getblocktemplate

↓

Template Parser

↓

Internal Template

↓

Job Builder

↓

Database

↓

Worker Sessions

↓

mining.notify
```

---

# Template Acquisition

Seymour periodically requests work from Bitcoin Core using:

```
getblocktemplate
```

The response includes:

- Previous block hash
- Block height
- Coinbase value
- Version
- NBits
- Current time
- Transactions
- Merkle data

---

# Template Parsing

The raw RPC response is converted into Seymour's internal template model.

Parsing validates:

- Required fields
- Data types
- Transaction structure
- Consensus values

Invalid templates are rejected.

---

# Internal Template Model

Each template contains:

- Template height
- Previous block hash
- Coinbase value
- Version
- NBits
- NTime
- Transaction list
- Merkle branches

The internal model is independent of the RPC response format.

---

# Job Generation

Each template produces one or more mining jobs.

A job includes:

- Job ID
- Coinbase Part 1
- Coinbase Part 2
- Merkle branches
- Version
- NBits
- NTime
- Work ID

Job identifiers are unique within the active job set.

---

# Database Persistence

Generated jobs are persisted before distribution.

Stored information includes:

- Job ID
- Template height
- Previous block hash
- Coinbase components
- Merkle branches
- Creation timestamp
- Active status

Persistence supports delayed share validation and operational diagnostics.

---

# Session Assignment

Jobs are distributed independently to each connected worker.

Each session records:

```
Job ID

↓

Assigned Difficulty

↓

Issue Time
```

This association remains valid until the job is retired.

---

# Job Distribution

After persistence, Seymour sends:

```
mining.notify
```

to eligible workers.

Each notification contains:

- Job ID
- Previous block hash
- Coinbase parts
- Merkle branches
- Version
- NBits
- NTime
- Clean Jobs flag

---

# Clean Jobs

When required, Seymour issues jobs with:

```
clean_jobs = true
```

Workers should discard obsolete work and begin mining the new template immediately.

---

# Template Refresh

Templates are refreshed whenever:

- A new block is detected.
- Bitcoin Core provides updated work.
- Pool policy requires regeneration.

Refreshing templates minimizes stale work.

---

# Job Retirement

Jobs eventually transition through:

```
Issued

↓

Active

↓

Historical

↓

Retired
```

Historical jobs remain available briefly for delayed share validation before removal.

---

# Relationship to VarDiff

Difficulty changes do not modify existing jobs.

Instead:

```
Difficulty Changes

↓

New Job Generated

↓

Job Assigned Difficulty Recorded
```

Older jobs preserve their original assigned difficulty.

---

# Error Handling

If template generation fails:

- Continue serving existing jobs when safe.
- Retry Bitcoin RPC.
- Record diagnostic information.
- Notify operators through logs.

Temporary RPC failures should not immediately interrupt mining.

---

# Performance

Template generation should:

- Minimize Bitcoin RPC requests.
- Avoid duplicate work generation.
- Reuse immutable transaction data where possible.
- Generate jobs quickly after template updates.

---

# Logging

Important events include:

- Template received
- Template parsed
- Job generated
- Job persisted
- Job distributed
- Template refresh
- Template failure

These logs provide visibility into the mining work pipeline.

---

# Future Enhancements

Future improvements may include:

- Incremental template updates
- Multiple template sources
- Template caching
- Cluster-wide distribution
- High-availability synchronization

These enhancements should preserve the existing lifecycle semantics.

---

# Engineering Principles

The Block Template subsystem follows these principles:

- Bitcoin Core provides blockchain truth.
- Seymour transforms templates into mining jobs.
- Jobs are immutable once issued.
- Sessions receive independent job assignments.
- Historical jobs remain available long enough for deterministic validation.

---

# Summary

The Block Template Lifecycle converts Bitcoin Core work into immutable mining jobs that are distributed to Stratum workers.

Its design ensures reliable work generation, deterministic validation, and efficient mining operation while preserving compatibility with the rest of the Seymour Pool Engine architecture.

---

# Next Step

Continue with:

**37-BLOCK-SUBMISSION-PIPELINE.md**
