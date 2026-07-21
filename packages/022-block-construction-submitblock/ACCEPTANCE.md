# Acceptance Criteria

- Migration 023 installs the block-candidate ledger.
- Full blocks serialize the 80-byte header, compact-size transaction count, coinbase, and template transactions.
- `submitblock` is called only for network-target candidates.
- Accepted and rejected RPC outcomes are persisted.
- Candidate status and history API routes are registered.
- Ruff and package tests pass.
