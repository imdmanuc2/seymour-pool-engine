# Seymour Pool Engine

**Version:** 1.0 (Development)

---

# Welcome

Seymour Pool Engine is a modern Bitcoin mining pool engine built from the ground up in Python.

Its goals are:

- Native Stratum server
- Native Bitcoin job generation
- Native share validation
- Variable Difficulty (VarDiff)
- Native statistics engine
- PostgreSQL persistence
- REST API
- Tight integration with Nexus Command Center

Unlike legacy mining software, Seymour is designed to be modular, testable, and maintainable while remaining compatible with existing ASIC miners using the standard Stratum protocol.

---

# Documentation Index

Read the documents in order.

| Document | Description |
|----------|-------------|
| **00-START-HERE.md** | Introduction and documentation guide |
| **01-ARCHITECTURE.md** | High-level system architecture |
| **02-INSTALLATION.md** | Installing Seymour Pool Engine |
| **03-CONFIGURATION.md** | Engine configuration and environment variables |
| **04-STRATUM-PROTOCOL.md** | Supported Stratum protocol implementation |
| **05-NATIVE-STATISTICS.md** | Native statistics engine |
| **06-DATABASE.md** | PostgreSQL schema and persistence |
| **07-API.md** | REST API reference |
| **08-VARDIFF.md** | Variable Difficulty implementation |
| **09-BLOCK-TEMPLATES.md** | Bitcoin block template generation |
| **10-SHARE-VALIDATION.md** | Share validation pipeline |
| **11-BLOCK-SUBMISSION.md** | Block candidate processing |
| **12-OPERATIONS.md** | Operating the engine |
| **13-TROUBLESHOOTING.md** | Diagnostics and troubleshooting |
| **14-ROADMAP.md** | Version roadmap |
| **15-DEVELOPER-GUIDE.md** | Development standards and contribution guide |

---

# Current Capabilities

Current Version 1.0 development includes:

- Native Stratum server
- Session management
- Bitcoin block template generation
- Coinbase construction
- Merkle tree generation
- Share validation
- Variable Difficulty (VarDiff)
- Block candidate detection
- PostgreSQL persistence
- Statistics API
- Native hashrate calculations
- Nexus integration

---

# System Overview

```
 ASIC Miners
      │
      ▼
+---------------------------+
| Seymour Stratum Server    |
+---------------------------+
             │
             ▼
+---------------------------+
| Seymour Dispatcher        |
+---------------------------+
      │     │      │
      │     │      │
      ▼     ▼      ▼
 Jobs Shares VarDiff
      │
      ▼
 PostgreSQL
      │
      ▼
 REST API
      │
      ▼
 Nexus Command Center
```

---

# Design Philosophy

Seymour follows several core engineering principles.

- Modular architecture
- Small, testable components
- Deterministic share validation
- Native telemetry
- PostgreSQL as the authoritative data store
- Production-first engineering
- Versioned package development
- Comprehensive automated testing

---

# Repository Structure

```
docs/
migrations/
packages/
scripts/
src/
tests/
```

### docs/

Project documentation.

### migrations/

Database schema migrations.

### packages/

Incremental feature packages used during development.

### scripts/

Installation, verification, and operational tooling.

### src/

Application source code.

### tests/

Automated test suite.

---

# Supported Platform

Current development targets:

- Linux
- Python 3.13+
- PostgreSQL
- Bitcoin Core
- Standard Stratum ASIC miners

---

# Relationship to Nexus

Seymour Pool Engine is the mining engine.

Nexus Command Center is the operational management platform.

Seymour owns mining.

Nexus owns infrastructure, CMDB, operations, automation, dashboards, and visualization.

---

# Development Status

Version 1.0 is under active development.

The current objective is to deliver a complete production-ready mining workflow before expanding into Version 1.1 capabilities.

---

# Getting Started

For new developers, begin with:

1. **01-ARCHITECTURE.md**
2. **02-INSTALLATION.md**
3. **03-CONFIGURATION.md**

These documents provide the foundation needed before exploring the individual engine components.
