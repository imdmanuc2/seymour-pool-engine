# Package 025 — Native Hashrate & Pool Statistics

Adds Seymour-native mining telemetry without MiningCore or CKPool dependencies.

## Features

- Pool hashrate for 1m, 5m, 15m, and 1h windows
- Worker hashrate and efficiency
- Worker confidence phases: connected, authorized, stabilizing, stable, stalled, disconnected
- Engine submission and session telemetry
- Query indexes for live Stratum statistics
- API routes under `/api/v1/statistics`

Hashrate is calculated from accepted assigned share work (`difficulty × 2^32`) over the selected rolling window. VarDiff history is used to reconstruct the difficulty in effect when each share was submitted.
