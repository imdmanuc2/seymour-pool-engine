# Native Statistics Engine

**Document:** `17-NATIVE-STATISTICS.md`  
**Version:** 1.0 (Development)

---

## Purpose

The Seymour Pool Engine Native Statistics Engine calculates mining telemetry directly from live Stratum activity and validated share submissions.

It removes the need to depend on external pool software such as CKPool or MiningCore for basic operational visibility.

The Native Statistics Engine is the authoritative source for:

- Pool hashrate
- Worker hashrate
- Active worker count
- Accepted shares
- Rejected shares
- Efficiency
- Rejection rate
- Last submitted share
- Last accepted share
- Engine submission rate

These values are exposed through the Seymour REST API and consumed by Nexus Command Center.

---

## Design Goals

The Native Statistics Engine is designed to provide:

- Accurate mining telemetry
- Low-latency API responses
- Rolling time-window calculations
- Independent worker statistics
- Pool-level aggregation
- Historical operational visibility
- Direct integration with Nexus
- No dependency on external mining software

---

## Architecture

```text
ASIC Miners
    |
    v
Seymour Stratum Server
    |
    v
Share Validation
    |
    v
PostgreSQL
    |
    v
Statistics Repository
    |
    v
Statistics Service
    |
    v
REST API
    |
    v
Nexus Command Center
```

Every statistic originates from data Seymour already owns.

---

## Source of Truth

The Native Statistics Engine uses Seymour's PostgreSQL database as its source of truth.

Primary tables include:

```text
seymour_engine.stratum_sessions
seymour_engine.stratum_submissions
seymour_engine.stratum_difficulty_history
seymour_engine.native_statistics_snapshots
```

The statistics layer does not trust miner-reported hashrate.

Instead, it estimates hashrate from accepted proof-of-work shares.

---

## Why Accepted Shares Matter

ASIC firmware may report an estimated hardware hashrate, but that value does not prove that the pool is receiving valid work.

Seymour calculates hashrate from accepted shares because accepted shares confirm that:

- The worker is connected
- The worker is authorized
- The worker received valid work
- The worker is hashing
- The worker is submitting shares
- The submitted shares pass validation

This makes share-derived hashrate more useful for pool operations than miner-reported estimates alone.

---

## Statistics Time Windows

Statistics are calculated over rolling time windows.

Current supported windows include:

```text
1m
5m
15m
1h
```

Future releases may add:

```text
6h
12h
24h
7d
30d
```

Each window serves a different purpose.

### 1 Minute

Useful for:

- Fast operational feedback
- Detecting new activity
- Immediate troubleshooting

This window is noisy and should not be used as a long-term performance measure.

### 5 Minutes

Useful for:

- Live dashboards
- Worker status
- Responsive pool monitoring

### 15 Minutes

Useful for:

- Stable operational hashrate
- Reduced short-term variance
- Pool health decisions

### 1 Hour

Useful for:

- Trend analysis
- Capacity planning
- Historical reporting

---

## Pool Overview Statistics

Pool-level statistics are available through:

```http
GET /api/v1/statistics/overview?window=5m
```

Example response:

```json
{
  "source": "seymour-native-stratum",
  "scope": {
    "type": "pool",
    "id": "btc-solo"
  },
  "window": "5m",
  "windowSeconds": 300,
  "calculatedAt": "2026-08-02T22:53:55.047693+00:00",
  "hashrate": 14431090114560.0,
  "activeWorkers": 2,
  "acceptedShares": 523,
  "rejectedShares": 0,
  "lastShareAt": "2026-08-02T17:53:50.689902-05:00",
  "lastAcceptedAt": "2026-08-02T17:53:50.689902-05:00",
  "totalShares": 523,
  "efficiency": 1.0,
  "rejectionRate": 0.0
}
```

---

## Worker Statistics

Worker statistics are available through:

```http
GET /api/v1/statistics/workers?window=5m
```

Typical worker fields include:

```text
workerName
sessionId
remoteHost
remotePort
hashrate
difficulty
acceptedShares
rejectedShares
lastShareAt
lastAcceptedAt
lastActivityAt
connectedAt
online
phase
efficiency
rejectionRate
```

Each worker is calculated independently.

---

## Worker Detail

Detailed statistics for a single worker are available through:

```http
GET /api/v1/statistics/workers/{worker_name}?window=5m
```

This endpoint is intended for:

- Worker detail pages
- Troubleshooting
- Historical inspection
- Nexus CMDB reconciliation

---

## Engine Statistics

Engine-level statistics are available through:

```http
GET /api/v1/statistics/engine?window=5m
```

Engine statistics may include:

- Submission rate
- Active sessions
- Processing activity
- Recent database writes
- Share processing throughput

These metrics describe Seymour itself rather than miner performance.

---

## Hashrate Calculation

Hashrate is estimated from accepted share difficulty over a selected time window.

Conceptually:

```text
Accepted Work
    /
Elapsed Time
    =
Estimated Hashrate
```

The exact implementation uses the accumulated accepted share difficulty and the selected window duration.

Returned hashrate values are expressed in:

```text
Hashes per second
```

For display:

```text
TH/s = hashrate / 1,000,000,000,000
```

---

## Short-Window Variance

Share-derived hashrate naturally varies over short periods.

For example:

- A five-minute estimate may temporarily read high
- A five-minute estimate may temporarily read low
- A fifteen-minute value is usually steadier
- A one-hour value is better for trend reporting

This does not necessarily indicate unstable hardware.

It reflects the statistical nature of proof-of-work share discovery.

---

## Active Worker Detection

A worker should be considered active only when current operational evidence supports it.

Recommended conditions include:

```text
online = true
lastActivityAt is recent
lastShareAt is recent
phase indicates active mining
```

Historical disconnected sessions must not count as active workers.

The workers endpoint may include offline historical workers, so consumers should filter using:

```text
online == true
```

---

## Worker Phases

Worker phases may include:

```text
connected
authorized
receiving-jobs
submitting-shares
hashrate-stabilizing
stable
stalled
disconnected
```

A worker can be connected before enough accepted work exists to estimate hashrate reliably.

During that period, user interfaces should show:

```text
Hashrate stabilizing
```

instead of misleadingly displaying:

```text
0 TH/s
```

---

## Accepted Shares

Accepted shares are valid submissions that satisfy the difficulty assigned to the job that produced them.

Accepted shares contribute to:

- Worker hashrate
- Pool hashrate
- Efficiency
- Activity status
- Historical reporting

---

## Rejected Shares

Rejected shares are submissions that fail validation.

Possible reasons include:

```text
low-difficulty-share
duplicate share
stale or unknown job
invalid version
invalid time
malformed submission
unauthorized worker
```

Rejected shares remain useful operational evidence and should not be silently discarded.

---

## Efficiency

Efficiency is calculated as:

```text
Accepted Shares
    /
Total Shares
```

Example:

```text
accepted = 523
rejected = 0
total = 523
efficiency = 1.0
```

An efficiency of `1.0` represents `100%`.

---

## Rejection Rate

Rejection rate is calculated as:

```text
Rejected Shares
    /
Total Shares
```

Example:

```text
accepted = 523
rejected = 0
total = 523
rejectionRate = 0.0
```

A sudden increase may indicate:

- Incorrect job handling
- Difficulty synchronization failure
- Network latency
- Stale work
- Firmware incompatibility
- Duplicate submissions
- Protocol errors

---

## Production VarDiff Validation Fix

During live ASIC testing, Seymour initially reported extremely high rejection rates.

Observed behavior included approximately:

```text
Accepted: 40–50
Rejected: approximately 12,000
```

The miners were functioning correctly.

The root cause was a job-difficulty synchronization defect.

Shares generated under an older difficulty were being validated against the worker's newer session difficulty.

The corrected implementation now:

- Associates every issued job with its assigned difficulty
- Issues a fresh job after each VarDiff change
- Validates shares against the original job difficulty
- Rejects jobs not issued to the current session
- Preserves recent job mappings for delayed valid submissions

After the fix, live production sessions showed:

```text
Worker 001
Accepted: 5354
Rejected: 0
Acceptance: 100%

Worker 002
Accepted: 5256
Rejected: 0
Acceptance: 100%
```

This production result validates the Native Statistics Engine and the underlying share accounting pipeline.

---

## Historical Data Considerations

Historical totals may include submissions generated before a software fix.

For operational health, dashboards should prefer:

- Current-session statistics
- Rolling-window statistics
- Post-deployment statistics

Lifetime totals should not be used as the only indicator of current health.

Historical rejected rows should remain in PostgreSQL as audit evidence.

---

## Native Statistics Snapshots

The table:

```text
seymour_engine.native_statistics_snapshots
```

stores calculated telemetry snapshots.

Snapshots may support:

- Faster dashboard rendering
- Historical charts
- Reporting
- Long-term trend analysis
- Reduced live query cost

---

## API Source Identifier

Statistics responses identify their source as:

```text
seymour-native-stratum
```

Consumers should use this value to distinguish Seymour-native telemetry from:

- CKPool telemetry
- MiningCore telemetry
- Miner-reported data
- Imported historical data

---

## Nexus Command Center Integration

Nexus consumes Native Statistics for:

- Home dashboards
- Pool cards
- Worker cards
- CMDB reconciliation
- Infrastructure Explorer
- Alerts
- Recommendations
- AI context
- Operations verification

The Pool Engine owns mining truth.

Nexus owns presentation, relationships, and operational workflows.

---

## CMDB Usage

Recommended CMDB mappings include:

```text
Pool CI
  current hashrate
  active worker count
  accepted shares
  rejected shares
  last accepted share
  health

Worker CI
  current hashrate
  difficulty
  online status
  phase
  last activity
  last share
```

The CMDB should consume the API for live state and use PostgreSQL only for deeper reconciliation or historical analysis.

---

## Health Logic

Suggested pool health rules:

### Online

```text
API reachable
Stratum reachable
activeWorkers > 0
lastAcceptedAt is recent
```

### Idle

```text
API reachable
Stratum reachable
activeWorkers == 0
```

### Degraded

```text
Workers connected
No accepted share within expected interval
Elevated rejection rate
```

### Offline

```text
API unreachable
or
Stratum unreachable
```

---

## Operational Commands

Pool overview:

```bash
curl -s \
  'http://127.0.0.1:8561/api/v1/statistics/overview?window=5m' |
python3 -m json.tool
```

Workers:

```bash
curl -s \
  'http://127.0.0.1:8561/api/v1/statistics/workers?window=5m' |
python3 -m json.tool
```

Engine:

```bash
curl -s \
  'http://127.0.0.1:8561/api/v1/statistics/engine?window=5m' |
python3 -m json.tool
```

---

## Troubleshooting

### API Returns Zero Statistics

Verify:

- The API service was restarted after deployment
- The API and Stratum services use the same environment file
- The database connection is correct
- Recent submissions exist
- Current workers are online

### Hashrate Is Lower Than Expected

Check:

- The selected time window
- Number of accepted shares
- Recent worker reconnects
- Current difficulty
- Worker phase

Short windows may be statistically noisy.

### Historical Workers Appear

Filter:

```text
online == true
```

Historical workers remain available for reporting but should not count as active.

### Rejection Rate Is High

Inspect:

- Reject reasons
- Current session IDs
- Job IDs
- VarDiff transitions
- Session-bound job mappings
- Miner reconnects

---

## Security

Statistics endpoints are read-only in Version 1.0.

Production recommendations include:

- Restrict API access to trusted networks
- Add TLS where remote access is required
- Use service authentication in future versions
- Avoid exposing the API directly to the public Internet

---

## Scalability

The Native Statistics Engine is designed to support growth from a few home miners to thousands of workers.

Scaling considerations include:

- Indexed submission queries
- Connection pooling
- Snapshot aggregation
- Retention policies
- Table partitioning
- Historical archiving
- Read replicas

---

## Future Enhancements

Possible future capabilities include:

- WebSocket streaming
- Historical charts
- Per-device telemetry
- Pool comparison
- Predictive hashrate analysis
- Prometheus export
- Alert thresholds
- Long-term performance reports
- AI-assisted anomaly detection

---

## Summary

The Native Statistics Engine turns validated Stratum activity into trustworthy operational telemetry.

It allows Seymour Pool Engine to prove that miners are connected, submitting valid work, and producing measurable hashrate without relying on external mining software.

This capability is foundational to Seymour Version 1.0 and to the wider Nexus integration.

---

## Next Step

Continue with:

**18-REST-API-REFERENCE.md**
