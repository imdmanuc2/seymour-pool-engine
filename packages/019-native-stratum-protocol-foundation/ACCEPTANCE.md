# Acceptance

- Package 018 migration is present.
- Migration 020 is recorded.
- Stratum persistence tables exist in `seymour_engine`.
- Ruff passes.
- Stratum protocol, dispatcher, and server tests pass.
- `/api/v1/stratum/status` and `/api/v1/stratum/sessions` are registered.
- `python -m seymour_pool_engine.stratum_runtime` starts the TCP listener.
- The bundled smoke client completes subscribe and authorize against the listener.
