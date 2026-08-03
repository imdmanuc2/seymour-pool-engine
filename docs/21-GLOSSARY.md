# Glossary

**Document:** 21-GLOSSARY.md

**Version:** 1.0 (Development)

---

# Purpose

This glossary defines common terminology used throughout the Seymour Pool Engine documentation.

The goal is to provide consistent definitions for developers, operators, and future contributors.

---

# Accepted Share

A submitted share that satisfies the difficulty assigned to the job and passes all validation checks.

Accepted shares contribute to worker and pool hashrate calculations.

---

# ASIC

Application-Specific Integrated Circuit.

Specialized hardware designed specifically for cryptocurrency mining.

---

# Block Candidate

A validated share whose hash satisfies the current Bitcoin network target.

A block candidate is eligible for submission to a Bitcoin node.

---

# Block Template

A mining job generated from the connected Bitcoin node containing:

- Previous block hash
- Coinbase transaction
- Merkle branches
- Version
- NBits
- NTime

---

# Coinbase Transaction

The first transaction in every Bitcoin block.

It creates the block reward and includes the miner's payout information.

---

# Difficulty

A measurement of how difficult it is to discover a valid proof-of-work solution.

Higher difficulty requires more hashing effort.

---

# Extranonce1

A unique value assigned by the Stratum server for each mining session.

---

# Extranonce2

A miner-generated value combined with Extranonce1 to create unique coinbase transactions.

---

# Hashrate

Estimated computational work performed by a miner or pool.

Usually displayed in:

- GH/s
- TH/s
- PH/s

---

# Job

A unit of mining work sent from the pool to a worker.

Each job contains all information necessary to construct a candidate block header.

---

# Merkle Branch

Hashes used to reconstruct the Merkle Root from the coinbase transaction.

---

# Native Statistics

Mining telemetry calculated directly from Seymour's validated share database rather than external mining software.

---

# NBits

Compact representation of the Bitcoin network target.

---

# Nonce

A 32-bit value modified by miners during proof-of-work.

---

# Pool Difficulty

Difficulty assigned by the pool for submitted shares.

It is independent of the Bitcoin network difficulty.

---

# Previous Block Hash

Hash of the current blockchain tip.

Included in every mining job.

---

# Proof of Work

The computational process used to discover hashes below the required target.

---

# Rejected Share

A submitted share that fails validation.

Examples include:

- Low difficulty
- Duplicate
- Stale
- Invalid version
- Invalid time

---

# Session

A single Stratum connection between a miner and Seymour.

---

# Share

A proof-of-work submission sent by a miner.

Most shares do not satisfy the Bitcoin network target but demonstrate useful mining work.

---

# Share Difficulty

The calculated difficulty represented by an individual submitted share.

---

# Solo Mining

Mining where a miner receives the full block reward if a valid block is discovered.

---

# Stratum

The protocol used for communication between mining software and mining pools.

---

# Template Height

The blockchain height associated with a mining job.

---

# VarDiff

Variable Difficulty.

Automatically adjusts worker difficulty to maintain consistent share submission rates.

---

# Version Rolling

A Stratum extension allowing miners to modify specific version bits to increase available search space.

---

# Worker

An individual mining device connected to Seymour.

A worker may represent:

- ASIC
- FPGA
- CPU miner
- GPU miner

---

# Work ID

Internal identifier associated with a generated mining job.

---

# Summary

This glossary provides standardized terminology for the Seymour Pool Engine documentation and should be updated whenever new platform concepts are introduced.
