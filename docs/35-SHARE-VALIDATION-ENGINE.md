# Share Validation Engine

**Document:** 35-SHARE-VALIDATION-ENGINE.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document defines the internal architecture of the Seymour Pool Engine Share Validation Engine.

The Share Validation Engine is responsible for determining whether every submitted share is valid, should be accepted, rejected, or submitted as a Bitcoin block candidate.

It is one of the core components of the Seymour mining pipeline.

---

# Design Goals

The validation engine is designed to provide:

- Deterministic validation
- Session isolation
- Protocol compliance
- High performance
- Complete auditability
- Accurate statistics

Every submitted share must follow the same validation pipeline.

---

# Validation Pipeline

```
mining.submit

↓

Parse Request

↓

Locate Session

↓

Locate Job

↓

Verify Session Ownership

↓

Load Assigned Difficulty

↓

Validate Parameters

↓

Construct Coinbase

↓

Construct Merkle Root

↓

Construct Block Header

↓

Double SHA256

↓

Calculate Share Difficulty

↓

Compare Against Pool Target

↓

Compare Against Network Target

↓

Accept / Reject

↓

Persist

↓

Update Statistics
```

---

# Input

A submitted share contains:

- Worker name
- Job ID
- Extranonce2
- NTime
- Nonce
- Version Bits (optional)

The validation engine treats all submitted values as untrusted until verified.

---

# Session Lookup

Validation begins by locating the active Stratum session.

The session provides:

- Worker identity
- Extranonce1
- Current protocol state
- Assigned jobs
- Version rolling negotiation

Shares referencing unknown sessions are rejected.

---

# Job Lookup

The submitted Job ID is used to retrieve the corresponding job.

Validation confirms:

- Job exists
- Job is active
- Job belongs to the submitting session

Jobs issued to other sessions are never accepted.

---

# Job Ownership

Each session maintains a bounded map of issued jobs.

```
Job ID

↓

Assigned Difficulty
```

Only jobs issued to the submitting session may be validated.

This prevents stale or foreign work from being accepted.

---

# Difficulty Selection

Validation uses the difficulty assigned when the job was created.

Current worker difficulty is **not** used for historical jobs.

This preserves correctness across VarDiff adjustments.

---

# Coinbase Construction

The validator reconstructs the complete coinbase transaction using:

- Coinbase Part 1
- Extranonce1
- Extranonce2
- Coinbase Part 2

The reconstructed transaction must exactly match the miner's expected work.

---

# Merkle Root Construction

The coinbase hash becomes the first Merkle tree leaf.

Each stored Merkle branch is applied in sequence until the Merkle Root is produced.

The resulting root is inserted into the block header.

---

# Block Header Construction

The validator constructs the 80-byte Bitcoin block header using:

- Version
- Previous Block Hash
- Merkle Root
- NTime
- NBits
- Nonce

When version rolling is enabled, negotiated version bits are applied before hashing.

---

# Hash Calculation

The completed header undergoes:

```
SHA256

↓

SHA256
```

The resulting hash determines the achieved share difficulty.

---

# Difficulty Calculation

The achieved difficulty is calculated from the resulting hash.

Validation compares:

```
Achieved Difficulty

↓

Assigned Pool Difficulty
```

Accepted shares meet or exceed the assigned pool target.

---

# Block Candidate Detection

If the resulting hash also satisfies the Bitcoin network target:

```
Accepted Share

↓

Block Candidate

↓

Bitcoin RPC Submission
```

Block candidates continue through the Block Submission Pipeline.

---

# Reject Conditions

Common reject reasons include:

- Unknown session
- Unknown job
- Session/job mismatch
- Duplicate share
- Low difficulty
- Invalid extranonce
- Invalid version bits
- Invalid timestamp
- Malformed request

Each rejection should produce a meaningful reason for operational diagnostics.

---

# Persistence

Every validated submission is recorded.

Typical fields include:

- Session ID
- Worker
- Job ID
- Accepted
- Reject reason
- Share hash
- Share difficulty
- Block candidate
- Header hex
- Timestamp

Persistence supports auditing, statistics, and troubleshooting.

---

# Statistics Integration

Accepted shares update:

- Worker statistics
- Pool statistics
- Native Statistics
- Efficiency calculations

Rejected shares update rejection metrics but do not contribute to hashrate estimation.

---

# Logging

Important events include:

- Share received
- Share accepted
- Share rejected
- Duplicate detected
- Block candidate
- Validation failure

Logs should support production diagnostics without exposing sensitive information.

---

# Performance

The validation engine operates within the Stratum request path.

It should:

- Minimize allocations
- Avoid unnecessary database queries
- Reuse immutable job data
- Execute deterministic calculations

Correctness always takes priority over micro-optimizations.

---

# Failure Handling

Unexpected validation failures should:

- Reject the offending share
- Preserve the Stratum session
- Continue servicing other workers
- Record sufficient diagnostic information

The engine should remain available even when individual validations fail.

---

# Engineering Principles

The Share Validation Engine follows these invariants:

- Sessions own jobs.
- Jobs own assigned difficulty.
- Validation is deterministic.
- Accepted shares become operational truth.
- Statistics derive only from validated shares.

These principles should remain stable across future releases.

---

# Future Enhancements

Potential future work includes:

- Parallel validation
- Hardware-specific optimizations
- Enhanced duplicate detection
- Additional protocol extensions
- Advanced validation telemetry

These enhancements should preserve existing validation semantics.

---

# Summary

The Share Validation Engine forms the core of the Seymour Pool Engine by transforming untrusted mining submissions into verified operational data.

Its deterministic validation pipeline ensures accurate statistics, reliable mining operation, and correct Bitcoin block candidate generation.

---

# Next Step

Continue with:

**36-BLOCK-TEMPLATE-LIFECYCLE.md**
