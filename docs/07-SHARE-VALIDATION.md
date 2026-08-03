# Share Validation

**Document:** 07-SHARE-VALIDATION.md

**Version:** 1.0 (Development)

---

# Purpose

Share validation is the core responsibility of the Seymour Pool Engine.

Every submitted share is independently reconstructed, hashed, validated, recorded, and classified before being accepted.

Only valid shares contribute toward miner statistics or become potential Bitcoin block candidates.

---

# Overview

Every mining submission follows the same pipeline.

```
Miner

↓

mining.submit

↓

Session Validation

↓

Job Validation

↓

Coinbase Construction

↓

Merkle Root

↓

Block Header

↓

Double SHA256

↓

Difficulty Calculation

↓

Duplicate Detection

↓

Accepted / Rejected

↓

Persist to PostgreSQL
```

No shortcuts are taken.

Every share is fully rebuilt before validation.

---

# Session Validation

The first validation step confirms the submission belongs to an active session.

Checks include:

- Authorized worker
- Active session
- Correct worker name
- Valid parameters

Invalid sessions are rejected immediately.

---

# Job Validation

Each submission references a Job ID.

Example

```
e189d39140ddaa17
```

The job must:

- Exist
- Still be active
- Belong to the submitting session

Unknown jobs return:

```
stale or unknown job
```

---

# Session-Based Job Tracking

Each issued mining job stores the difficulty that existed when it was created.

```
Session

↓

Job

↓

Assigned Difficulty
```

When a share is submitted:

```
Submitted Job

↓

Lookup Difficulty

↓

Validate Against Original Difficulty
```

This prevents Variable Difficulty changes from incorrectly rejecting valid shares.

This design dramatically reduced false "low difficulty share" rejections.

---

# Coinbase Construction

The validator reconstructs the exact coinbase transaction.

```
coinbase1

+

extranonce1

+

extranonce2

+

coinbase2
```

The resulting transaction is identical to what the miner hashed.

---

# Coinbase Hash

The completed coinbase undergoes:

```
SHA256

↓

SHA256
```

Result:

```
Coinbase Hash
```

---

# Merkle Root

Starting with the coinbase hash:

```
Coinbase Hash

↓

Merkle Branch 1

↓

Merkle Branch 2

↓

...

↓

Merkle Root
```

Every branch undergoes double SHA256.

The final Merkle Root becomes part of the block header.

---

# Block Header Construction

The validator rebuilds the full Bitcoin block header.

Fields include:

- Version
- Previous Block Hash
- Merkle Root
- nTime
- nBits
- Nonce

The resulting header is exactly 80 bytes.

---

# Version Rolling

If negotiated by the miner:

Submitted version bits are merged with the template version using the negotiated version mask.

Invalid version bits are rejected.

---

# Double SHA256

The completed block header undergoes:

```
SHA256

↓

SHA256
```

Result:

```
256-bit Block Hash
```

---

# Share Difficulty

The resulting hash is converted into achieved difficulty.

Conceptually:

```
Difficulty 1 Target

÷

Hash Value

=

Achieved Difficulty
```

Higher difficulty indicates a better share.

---

# Assigned Difficulty

The assigned difficulty is retrieved from the job that produced the share.

Example

```
Job

↓

Difficulty 5376
```

Validation compares:

```
Achieved Difficulty

>=

Assigned Difficulty
```

If true:

```
Accepted
```

Otherwise:

```
Rejected
```

---

# Block Candidate Detection

The same hash is also compared against the Bitcoin network target.

```
Hash

↓

Network Target
```

If the hash satisfies network difficulty:

```
Block Candidate
```

The block is submitted to Bitcoin Core.

---

# Duplicate Detection

Every share receives a submission fingerprint.

Fingerprint components include values such as:

- Worker
- Job
- Extranonce2
- nTime
- Nonce

Previously seen fingerprints are rejected.

This prevents:

- Duplicate submissions
- Network retries
- Firmware retransmission

---

# Database Recording

Every validated share is written to PostgreSQL.

Information includes:

- Worker
- Session
- Job
- Timestamp
- Accepted
- Reject reason
- Share difficulty
- Block candidate
- Header
- Hash

This provides a permanent audit trail.

---

# Accepted Shares

Accepted shares contribute to:

- Worker hashrate
- Pool hashrate
- Efficiency
- Native statistics
- Historical reporting

Accepted shares do not necessarily solve Bitcoin blocks.

Most accepted shares are ordinary proof-of-work shares.

---

# Rejected Shares

Rejected shares are classified with a reason.

Examples include:

```
low-difficulty-share

duplicate share

invalid job

invalid version

invalid time

malformed

unauthorized worker
```

Reject reasons are stored for diagnostics.

---

# Block Submission

When a valid block candidate is discovered:

```
Share

↓

Candidate Block

↓

Bitcoin Core submitblock()

↓

Accepted / Rejected
```

Bitcoin Core performs final consensus validation.

---

# Native Statistics

Validation immediately updates statistics.

Metrics include:

- Accepted shares
- Rejected shares
- Efficiency
- Last accepted share
- Worker hashrate
- Pool hashrate

Statistics become available through the REST API without requiring external mining software.

---

# Operational Logging

Important validation events are logged.

Examples include:

```
JOB

VARDIFF_JOB

duplicate share

block candidate

accepted

rejected
```

Logging is intended for diagnostics and operational visibility.

---

# Reliability

The validation pipeline is designed to be:

- Deterministic
- Reproducible
- Auditable
- Protocol compliant
- Independent of miner firmware

Every accepted share can be reconstructed and verified from stored database records.

---

# Relationship to Other Components

Share Validation depends on:

- Session Manager
- Job Engine
- Variable Difficulty
- Bitcoin Templates
- PostgreSQL

It supplies data to:

- Native Statistics
- REST API
- Nexus Command Center
- CMDB
- Alerting
- Historical reporting

---

# Next Step

Continue with:

**08-VARIABLE-DIFFICULTY.md**
