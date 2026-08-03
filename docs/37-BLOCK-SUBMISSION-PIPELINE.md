# Block Submission Pipeline

**Document:** 37-BLOCK-SUBMISSION-PIPELINE.md

**Version:** 1.0 (Engineering Specification)

---

# Purpose

This document defines the internal architecture of the Seymour Pool Engine Block Submission Pipeline.

The Block Submission Pipeline is responsible for detecting valid Bitcoin block candidates and submitting them to Bitcoin Core.

It represents the final stage of the mining workflow.

---

# Design Goals

The Block Submission Pipeline is designed to provide:

- Reliable block submission
- Deterministic validation
- Fast propagation
- Complete auditing
- Production reliability
- Minimal submission latency

---

# Overview

```
Mining Worker

↓

Share Validation

↓

Accepted Share

↓

Network Target Check

↓

Block Candidate

↓

Bitcoin RPC

↓

submitblock

↓

Bitcoin Network
```

---

# Entry Point

The pipeline begins after a share has passed all validation checks.

Validation confirms:

- Session ownership
- Job ownership
- Assigned difficulty
- Header integrity
- Share hash

Only accepted shares continue.

---

# Block Candidate Detection

Every accepted share is compared against the current Bitcoin network target.

```
Share Hash

↓

Network Target

↓

Candidate?
```

If the network target is met, the share becomes a block candidate.

---

# Candidate Verification

Before submission Seymour verifies:

- Template height
- Previous block hash
- Coinbase
- Merkle root
- Block header
- Header hash

Verification prevents malformed block submissions.

---

# Block Construction

The full Bitcoin block is assembled from:

- Block header
- Coinbase transaction
- Transaction list
- Witness commitment (when applicable)

The resulting block must conform to Bitcoin consensus rules.

---

# Bitcoin RPC

Version 1.0 submits candidates using:

```
submitblock
```

The request is sent to the configured Bitcoin Core node.

---

# Submission Results

Possible responses include:

- Accepted
- Duplicate
- Invalid
- Rejected
- RPC failure

Every response is recorded.

---

# Persistence

Successful and unsuccessful submissions are stored for auditing.

Typical information includes:

- Block height
- Block hash
- Submission time
- RPC result
- Worker
- Session
- Job ID

---

# Logging

Important events include:

- Candidate detected
- Block assembled
- RPC request
- RPC response
- Successful submission
- Failed submission

Logs should provide sufficient information for post-incident analysis.

---

# Failure Handling

If submission fails:

- Preserve the candidate information.
- Record the RPC response.
- Continue mining.
- Do not interrupt connected workers.

Mining availability always takes precedence.

---

# Statistics

Successful candidates update:

- Block counters
- Operational metrics
- Pool statistics
- Future historical reporting

Version 1.0 focuses on immediate operational visibility.

---

# Nexus Integration

Future Nexus integrations may display:

- Candidate history
- Submission history
- Block discoveries
- RPC health
- Submission latency

These capabilities consume Seymour's REST API rather than direct database access.

---

# Security

Only trusted Bitcoin Core nodes should receive block submissions.

RPC credentials should be:

- Protected
- Rotated
- Excluded from source control

---

# Performance

The submission pipeline should:

- Minimize RPC latency
- Avoid duplicate submissions
- Preserve candidate information
- Continue mining without interruption

Workers should never pause while a block is being submitted.

---

# Future Enhancements

Potential future improvements include:

- Multiple Bitcoin Core nodes
- Automatic failover
- Submission verification
- Distributed submission
- Block propagation metrics
- High-availability RPC

---

# Engineering Principles

The Block Submission Pipeline follows these principles:

- Every accepted share is evaluated.
- Only network-valid shares become candidates.
- Candidate validation is deterministic.
- Bitcoin Core remains the authority for final acceptance.
- Mining continues regardless of submission outcome.

---

# Summary

The Block Submission Pipeline is the final stage of the Seymour mining process.

It transforms validated network-quality shares into Bitcoin block submissions while preserving complete operational visibility and maintaining uninterrupted mining service.

---

# Next Step

Continue with:

**38-DATABASE-MIGRATION-STANDARDS.md**
