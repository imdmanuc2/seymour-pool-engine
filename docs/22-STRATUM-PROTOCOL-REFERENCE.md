# Stratum Protocol Reference

**Document:** 22-STRATUM-PROTOCOL-REFERENCE.md

**Version:** 1.0 (Development)

---

# Purpose

This document describes the Stratum mining protocol as implemented by the Seymour Pool Engine.

It is intended for developers implementing mining clients, debugging ASIC communication, or extending the Seymour Stratum server.

---

# Overview

Stratum is the communication protocol between mining hardware and the mining pool.

Its responsibilities include:

- Session establishment
- Worker authorization
- Job distribution
- Difficulty management
- Share submission
- Block candidate submission

---

# Connection Flow

A typical Seymour connection follows this sequence.

```
TCP Connection
        ↓
mining.subscribe
        ↓
Subscription Response
        ↓
mining.set_difficulty
        ↓
mining.notify
        ↓
mining.authorize
        ↓
Authorization Success
        ↓
Mining Begins
        ↓
mining.submit
        ↓
Share Validation
```

---

# Transport

Version 1.0 uses:

- TCP
- JSON-RPC
- Line-delimited messages
- Persistent connections

---

# Session Lifecycle

Each miner establishes a Stratum session.

A session contains:

- Session ID
- Worker name
- Extranonce1
- Extranonce2 size
- Difficulty
- Current jobs
- Connection timestamps
- Statistics

---

# mining.subscribe

The first request sent by a miner.

Example:

```json
{
    "id":1,
    "method":"mining.subscribe",
    "params":[
        "AvalonMiner"
    ]
}
```

The response assigns:

- Subscription ID
- Extranonce1
- Extranonce2 size

---

# mining.authorize

Authenticates a worker.

Example

```json
{
    "id":2,
    "method":"mining.authorize",
    "params":[
        "wallet.worker",
        "x"
    ]
}
```

Successful authorization enables mining.

---

# mining.notify

Distributes a new mining job.

A notification contains:

- Job ID
- Previous block hash
- Coinbase parts
- Merkle branches
- Version
- NBits
- NTime
- Clean Jobs flag

---

# mining.set_difficulty

Updates pool difficulty.

Example

```json
{
    "method":"mining.set_difficulty",
    "params":[4096]
}
```

New work issued after a difficulty change uses the new assigned difficulty.

---

# mining.submit

Submits a completed share.

Typical parameters include:

- Worker
- Job ID
- Extranonce2
- NTime
- Nonce
- Version Bits (optional)

---

# Share Validation

Every submitted share is validated.

Validation includes:

- Job lookup
- Session ownership
- Difficulty
- Merkle calculation
- Header construction
- Double SHA256
- Network target
- Pool target

Only validated shares are accepted.

---

# Job Management

Each issued job belongs to a specific Stratum session.

Jobs include:

- Job ID
- Assigned difficulty
- Previous block hash
- Template height
- Coinbase
- Merkle branches

Jobs remain available briefly after newer work is issued to permit valid delayed submissions.

---

# Variable Difficulty

VarDiff adjusts worker difficulty automatically.

Objectives:

- Stable submission intervals
- Reduced bandwidth
- Efficient validation
- Consistent worker load

Difficulty adjustments trigger:

1. mining.set_difficulty

2. mining.notify

New jobs are issued immediately after difficulty changes.

---

# Job-Difficulty Synchronization

Beginning with Version 1.0, Seymour permanently associates each job with the difficulty active when the job was issued.

During share validation:

```
Submitted Job

↓

Assigned Difficulty

↓

Validation

↓

Accept / Reject
```

This prevents valid shares from being rejected after VarDiff changes.

---

# Extranonce

Seymour assigns:

- Extranonce1
- Extranonce2 Size

Miners generate Extranonce2 for every share.

Together they produce unique coinbase transactions.

---

# Version Rolling

Version rolling is supported when negotiated.

Validation ensures submitted version bits remain inside the negotiated mask.

---

# Reject Reasons

Common reject reasons include:

- low-difficulty-share
- duplicate share
- stale or unknown job
- invalid version
- invalid time
- malformed submission
- unauthorized worker

Reject reasons are preserved for operational diagnostics.

---

# Block Candidates

When a share satisfies the Bitcoin network target:

```
Share

↓

Block Candidate

↓

Bitcoin RPC

↓

Block Submission
```

Successful block candidates are submitted automatically.

---

# Compatibility

Version 1.0 is designed for compatibility with standard Stratum miners while incorporating Seymour-specific operational improvements.

Current compatibility testing includes:

- Avalon ASIC miners
- CPU miners
- Standard Stratum clients

Additional hardware will be validated over future releases.

---

# Logging

Important protocol events include:

- Connection opened
- Subscribe
- Authorize
- Job issued
- Difficulty change
- Share received
- Share accepted
- Share rejected
- Connection closed

These events provide a complete operational timeline.

---

# Security

Version 1.0 assumes trusted internal networks.

Future versions may introduce:

- TLS
- Authentication enhancements
- Rate limiting
- Worker policies

---

# Summary

The Seymour Stratum implementation follows the standard Stratum protocol while extending it with production-grade job tracking, Variable Difficulty synchronization, detailed validation, and comprehensive operational telemetry.
