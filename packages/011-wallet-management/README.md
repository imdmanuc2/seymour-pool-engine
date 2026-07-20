# Package 011 — Wallet Management

Adds managed wallet metadata and worker payout addresses to Seymour Pool Engine.

## Capabilities

- Pool, operator, developer, payout, reserve, and cold-storage wallet records
- Mainnet, testnet, and regtest separation
- Mandatory active developer-wallet modeling
- Public address validation and lifecycle state
- Wallet event history
- Per-worker, per-coin payout addresses
- Secret references only; private keys and seed phrases are never returned by the API

## Install

Run `scripts/doctor.sh`, `scripts/install.sh`, and `scripts/verify.sh`.
