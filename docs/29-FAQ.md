# Frequently Asked Questions (FAQ)

**Document:** 29-FAQ.md

**Version:** 1.0 (Development)

---

# Purpose

This document answers frequently asked questions about the Seymour Pool Engine.

It is intended for operators, developers, and anyone evaluating or deploying the platform.

---

# General

## What is the Seymour Pool Engine?

The Seymour Pool Engine is a native Bitcoin mining pool engine designed for production environments.

It provides:

- Native Stratum server
- Share validation
- Variable Difficulty (VarDiff)
- Native Statistics
- REST API
- PostgreSQL persistence
- Bitcoin RPC integration

---

## Is Seymour a mining pool?

Yes.

Seymour is a complete mining pool engine capable of managing mining workers, validating shares, generating statistics, and submitting valid block candidates to Bitcoin Core.

---

## Is Seymour tied to Nexus Command Center?

No.

The Seymour Pool Engine operates independently.

Nexus Command Center integrates with Seymour through its REST API but is a separate application.

---

## Can Seymour operate without Nexus?

Yes.

All mining functionality operates independently of Nexus.

---

# Mining

## Does Seymour support solo mining?

Yes.

Version 1.0 is focused on Bitcoin solo mining.

---

## Does Seymour support pooled mining?

Support for additional pool models is planned for future releases.

---

## Which mining hardware is supported?

Version 1.0 has been tested with:

- Avalon ASIC miners
- CPU miners
- Standard Stratum-compatible clients

Additional hardware will be validated over time.

---

## Does Seymour support Variable Difficulty?

Yes.

VarDiff automatically adjusts worker difficulty to maintain efficient share submission rates.

---

## Does Seymour support version rolling?

Yes.

Version rolling is supported when negotiated by compatible miners.

---

# Statistics

## How is hashrate calculated?

Hashrate is estimated using accepted shares within configurable time windows.

The engine uses its Native Statistics system rather than relying on external mining software.

---

## Why does hashrate change?

Hashrate is an estimate and naturally fluctuates over shorter time windows.

Longer windows generally provide a more stable estimate.

---

## Why are there multiple statistics windows?

Different windows serve different purposes:

- 1 minute – Immediate activity
- 5 minutes – Operational monitoring
- 15 minutes – Dashboard display
- 1 hour – Trend analysis

---

# Database

## Which database is required?

Version 1.0 uses PostgreSQL.

---

## Can another database be used?

Not currently.

The storage layer is designed around PostgreSQL.

---

## Should the database be modified directly?

No.

Schema changes should always be performed through migrations.

---

# REST API

## Is the API versioned?

Yes.

Version 1.0 uses:

```
/api/v1/
```

---

## Does the API require authentication?

Version 1.0 assumes deployment on trusted networks.

Future releases may introduce API authentication.

---

## Can third-party software use the API?

Yes.

The REST API is intended for integration with dashboards, automation, and external tools.

---

# Configuration

## Where is configuration stored?

Typically in environment files referenced by systemd or local development environments.

---

## Should secrets be committed to Git?

No.

Passwords, RPC credentials, and private keys should never be committed to source control.

---

# Development

## How should code be formatted?

Use Ruff.

```bash
ruff format
```

---

## How are tests run?

Use pytest.

```bash
pytest
```

---

## Is documentation required for new features?

Yes.

Significant features should include corresponding documentation updates.

---

# Operations

## How do I verify Seymour is healthy?

Check:

- systemd services
- REST API
- Stratum connectivity
- PostgreSQL
- Native Statistics
- Worker activity

---

## Where are logs located?

Most production deployments use systemd journals.

Example:

```bash
journalctl -fu seymour-pool-engine-stratum
```

---

## How should backups be performed?

Back up:

- PostgreSQL database
- Configuration files
- Environment files
- Migration history

Regular restore testing is recommended.

---

# Project

## Is Seymour open source?

Refer to the project's LICENSE file for current licensing information.

---

## Can I contribute?

Yes.

See:

**27-CONTRIBUTING.md**

---

## Where should I report bugs?

Use the project's GitHub issue tracker.

When reporting issues, include:

- Version
- Logs
- Reproduction steps
- Configuration summary
- Expected behavior
- Actual behavior

---

# Roadmap

## What comes after Version 1.0?

Future releases may include:

- Historical reporting
- Additional miner compatibility
- Expanded REST APIs
- Enterprise features
- AI-assisted diagnostics
- Distributed deployments

See:

**28-ROADMAP.md**

---

# Summary

This FAQ provides quick answers to common questions about the Seymour Pool Engine.

For detailed information, refer to the architecture, development, API, configuration, troubleshooting, and operations documentation included with the project.

---

# Next Step

Continue with:

**30-APPENDIX-EXAMPLES.md**
