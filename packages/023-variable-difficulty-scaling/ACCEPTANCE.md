# Acceptance Criteria

- Migration 024 is recorded.
- Session VarDiff state columns exist.
- Difficulty history table exists.
- Fast workers receive higher difficulty and slow workers receive lower difficulty.
- Retargeting is damped, bounded, and respects minimum/maximum difficulty.
- `mining.set_difficulty` is emitted after a successful retarget.
- `/api/v1/vardiff/status` and `/api/v1/vardiff/history` are registered.
- Ruff and Package 023 tests pass.
