# Job Engine

**Document:** 09-JOB-ENGINE.md

**Version:** 1.0 (Development)

---

# Purpose

The Job Engine is responsible for creating, managing, and distributing mining jobs.

It continuously converts Bitcoin Core block templates into Stratum jobs that ASIC miners can process.

Every accepted share submitted to Seymour originates from a job produced by the Job Engine.

---

# Responsibilities

The Job Engine is responsible for:

- Requesting block templates
- Building Stratum jobs
- Assigning unique Job IDs
- Constructing coinbase transactions
- Building Merkle trees
- Managing clean jobs
- Recording jobs
- Distributing jobs to workers
- Coordinating with Variable Difficulty

---

# Architecture

```
Bitcoin Core

↓

getblocktemplate

↓

Template Service

↓

Job Engine

↓

Stratum Dispatcher

↓

Mining Workers
```

---

# Block Templates

The Job Engine requests block templates from Bitcoin Core.

Each template contains:

- Previous block hash
- Version
- nBits
- nTime
- Coinbase value
- Transactions
- Transaction count

The template becomes the foundation for every mining job.

---

# Job Creation

Each mining job receives a unique identifier.

Example

```
98d3f424643c5cc0
```

Job IDs uniquely identify work issued to miners.

They are also used later during share validation.

---

# Job Contents

Every Stratum job contains:

- Job ID
- Previous Block Hash
- Coinbase Part 1
- Coinbase Part 2
- Merkle Branches
- Version
- nBits
- nTime
- Clean Jobs Flag

These values are transmitted directly to miners.

---

# Coinbase Construction

The Job Engine divides the coinbase transaction into two parts.

```
coinbase1

+

Extranonce

+

coinbase2
```

The miner inserts:

- Extranonce1
- Extranonce2

before hashing.

---

# Merkle Branch Generation

Transactions supplied by Bitcoin Core are converted into a Merkle tree.

Rather than transmitting every transaction, Seymour sends only the Merkle branches required for reconstruction.

Example:

```
Coinbase Hash

↓

Branch 1

↓

Branch 2

↓

Branch 3

↓

Merkle Root
```

This minimizes network traffic while remaining protocol compliant.

---

# Clean Jobs

When a new block template arrives, Seymour issues:

```
clean_jobs = true
```

This tells miners to abandon obsolete work and immediately begin mining on the newest block.

---

# Variable Difficulty Integration

Whenever VarDiff changes worker difficulty:

```
Difficulty Change

↓

New Job

↓

mining.notify
```

The new job is permanently associated with the difficulty active when it was created.

---

# Job Persistence

Every generated job is written to PostgreSQL.

Stored information includes:

- Job ID
- Block height
- Previous block hash
- Coinbase
- Merkle branches
- Version
- nBits
- nTime
- Source
- Timestamp

Jobs remain available for later validation.

---

# Session Association

Jobs are issued to individual worker sessions.

Each session tracks recently issued jobs.

Example:

```
Session

↓

Job A

Difficulty 5376

↓

Job B

Difficulty 10752

↓

Job C

Difficulty 10752
```

This enables accurate validation of delayed submissions.

---

# Job Expiration

Jobs eventually become obsolete.

Reasons include:

- New Bitcoin block
- Clean job update
- Worker disconnect
- Session expiration

Expired jobs are no longer accepted.

---

# Job Lookup

When a share arrives:

```
Submitted Job ID

↓

Database Lookup

↓

Job Retrieved

↓

Validation Begins
```

If the job cannot be located:

```
stale or unknown job
```

is returned to the miner.

---

# Block Template Refresh

The Job Engine automatically refreshes jobs whenever:

- Bitcoin Core announces a new block
- Transactions significantly change
- Clean jobs are required
- Variable Difficulty generates replacement work

---

# Native Statistics

Jobs contribute to:

- Active workers
- Current mining height
- Pool activity
- Share accounting
- Historical reporting

---

# Logging

Typical Job Engine log entries include:

```
JOB

clean_jobs=true

height=...

prevhash=...

job=...
```

These logs simplify troubleshooting and operational analysis.

---

# Design Goals

The Job Engine is designed to be:

- Deterministic
- Database-backed
- Fault tolerant
- Protocol compliant
- High performance
- Horizontally scalable

---

# Relationship to Other Components

The Job Engine works closely with:

- Bitcoin Core
- Template Service
- Stratum Dispatcher
- Variable Difficulty
- Share Validation
- PostgreSQL

Together they form the core mining pipeline.

---

# Future Enhancements

Future versions may include:

- Template pre-generation
- Multi-chain support
- Multi-algorithm support
- Distributed job generation
- Cluster synchronization

---

# Next Step

Continue with:

**10-DATABASE-SCHEMA.md**
