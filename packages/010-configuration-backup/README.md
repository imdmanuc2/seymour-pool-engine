# Package 010 — Configuration & Backup

Adds database-backed, immutable and auditable configuration management for Seymour Pool Engine.

## Capabilities

- Supported configuration domains for engine, pools, coins, RPC, Stratum, wallet references, economics, monitoring, API, and security.
- Validation before activation.
- Immutable revision history and rollback by revision.
- SHA-256 checksummed export and import.
- Import/export audit records.
- Mandatory developer-fee validation: the fee cannot be disabled or reduced below 0.75%.

## Install

```bash
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
