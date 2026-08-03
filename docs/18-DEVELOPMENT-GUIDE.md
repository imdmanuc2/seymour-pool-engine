# Development Guide

**Document:** 18-DEVELOPMENT-GUIDE.md

**Version:** 1.0 (Development)

---

# Purpose

This guide explains how to develop, test, debug, and contribute to the Seymour Pool Engine.

It is intended for developers working on the engine itself and for contributors integrating Seymour with external systems such as Nexus Command Center.

---

# Development Philosophy

Seymour follows several engineering principles.

- Build production-quality software.
- Keep components loosely coupled.
- Make every feature observable.
- Prefer simple solutions over clever ones.
- Preserve backward compatibility whenever practical.
- Finish Version 1.0 before expanding scope.

---

# Repository Layout

```
src/
tests/
docs/
migrations/
scripts/
packaging/
```

---

# Source Tree

```
src/seymour_pool_engine/

api/
config/
database/
engines/
repositories/
services/
stratum/
utilities/
```

Each directory has a single responsibility.

---

# Major Components

The engine consists of several independent layers.

```
REST API

↓

Services

↓

Repositories

↓

PostgreSQL
```

```
Stratum

↓

Share Validation

↓

Repositories

↓

PostgreSQL
```

Keeping these layers separate simplifies testing.

---

# Development Environment

Recommended tools:

- Python virtual environment
- Ruff
- Pytest
- PostgreSQL
- Git
- systemd
- curl

---

# Virtual Environment

Activate before development.

```bash
source .venv/bin/activate
```

---

# Formatting

Format code before committing.

```bash
ruff format
```

---

# Linting

Run Ruff.

```bash
ruff check
```

Correct all reported issues whenever practical.

---

# Testing

Run the complete test suite.

```bash
pytest
```

Individual tests may also be executed.

Example:

```bash
pytest tests/test_stratum_dispatcher.py
```

---

# Database Migrations

Schema changes must be implemented through migrations.

Never modify production tables manually.

Migration responsibilities include:

- schema creation
- indexes
- constraints
- data migration
- rollback support

---

# Configuration

Configuration belongs in environment files.

Examples include:

- database settings
- API ports
- Stratum ports
- logging
- RPC credentials

Application code should never contain production secrets.

---

# Logging

Every subsystem should produce structured log messages.

Important events include:

- startup
- shutdown
- connections
- authorization
- job creation
- share validation
- VarDiff
- block submission
- errors

Logs are critical for diagnosing mining problems.

---

# Share Validation

The validation pipeline must remain deterministic.

Every submitted share should produce one of two outcomes.

Accepted

or

Rejected

Rejected shares should include a reason whenever possible.

---

# VarDiff

Variable Difficulty should:

- maintain stable share intervals
- issue new jobs after difficulty changes
- preserve previous job difficulty
- avoid invalidating in-flight work

The VarDiff implementation is critical to mining stability.

---

# REST API

REST endpoints should:

- remain versioned
- return consistent JSON
- avoid breaking existing clients
- expose operational information
- avoid unnecessary database work

---

# Native Statistics

Statistics should be calculated from validated shares.

Never estimate statistics from:

- miner-reported hashrate
- dashboard values
- external pools

Validated work is the authoritative source.

---

# Documentation

Major features should include documentation updates.

Whenever possible:

- update architecture
- update API reference
- update troubleshooting
- update developer guide

Documentation should evolve alongside code.

---

# Debugging

Useful tools include:

```bash
journalctl
```

```bash
curl
```

```bash
psql
```

```bash
pytest
```

```bash
ruff
```

---

# Git Workflow

Typical workflow:

```
Create feature

↓

Implement

↓

Test

↓

Document

↓

Commit

↓

Push

↓

Review
```

---

# Commit Messages

Commit messages should describe the completed work.

Example:

```
Fix VarDiff job difficulty synchronization

```

Avoid vague commits such as:

```
Fix stuff

```

---

# Code Reviews

Review changes for:

- correctness
- readability
- performance
- documentation
- testing
- backward compatibility

---

# Performance

Before optimizing:

Measure.

After optimizing:

Measure again.

Production evidence should guide optimization decisions.

---

# Version 1.0 Priorities

Current priorities include:

- Stratum stability
- Share validation
- Native statistics
- REST API
- Nexus integration
- Documentation
- Packaging

Ideas beyond Version 1.0 should be added to the roadmap rather than interrupting current objectives.

---

# Future Development

Potential Version 1.1 topics include:

- multi-pool federation
- AI analysis
- distributed pool clusters
- advanced reporting
- WebSocket telemetry
- Prometheus integration

---

# Summary

The Seymour Pool Engine is designed to be modular, testable, and production-ready.

Consistent engineering practices help ensure reliability while allowing the platform to continue growing without unnecessary complexity.

---

# Next Step

Continue with:

**20-TROUBLESHOOTING.md**
