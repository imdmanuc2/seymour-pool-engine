# Acceptance

- `mining.submit` uses an active persisted job.
- Malformed, stale, duplicate, and low-difficulty shares return Stratum errors.
- Accepted shares meet the assigned target.
- Block candidates are identified against `nBits`.
- Hash, achieved difficulty, header, and rejection reason are persisted.
- Ruff and Package 021 tests pass.
