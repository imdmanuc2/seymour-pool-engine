# Package 012 — Payout Engine

Adds durable payout batches, payout items, lifecycle events, eligibility queries,
manual approval/execution state transitions, transaction recording, and API routes.

The package records payout intent and results. It does not hold private keys or sign
transactions; blockchain RPC execution is intentionally delegated to a later secured executor.
