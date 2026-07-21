# Acceptance Criteria

- Package 019 migration is present.
- Migration 021 creates the template store and extends Stratum jobs.
- Bitcoin Core `getblocktemplate` is requested with SegWit support.
- RPC templates are validated and converted into typed models.
- Coinbase parts preserve the extranonce1/extranonce2 insertion gap.
- Merkle branches are generated from template transaction hashes.
- Authorizing a worker uses the latest persisted job or refreshes from Bitcoin Core.
- `/api/v1/templates/status` and `/api/v1/templates/refresh` are registered.
- Ruff and focused tests pass.
