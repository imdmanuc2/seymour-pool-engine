# Connecting Your First Miner

**Version:** 1.0 (Development)

---

# Purpose

This guide walks through connecting your first ASIC miner to Seymour Pool Engine.

By the end of this guide you will have:

- Seymour Stratum running
- Bitcoin Core synchronized
- An ASIC connected
- Shares being accepted
- Native statistics reporting hashrate

---

# Prerequisites

Before continuing, verify:

- Seymour Pool Engine is installed
- Bitcoin Core is fully synchronized
- PostgreSQL is running
- Seymour API is running
- Seymour Stratum is running

Verify services:

```bash
sudo systemctl status seymour-pool-engine-api
```

```bash
sudo systemctl status seymour-pool-engine-stratum
```

Both should report:

```
Active: active (running)
```

---

# Verify Bitcoin RPC

Confirm Seymour can communicate with Bitcoin Core.

```bash
curl \
http://127.0.0.1:8561/api/v1/health
```

Expected result:

```
bitcoin:
    status: online
```

---

# Configure Your Miner

On your ASIC, create a new mining profile.

Example:

Pool URL

```
stratum+tcp://192.168.1.169:3336
```

Worker

```
YOUR_BITCOIN_ADDRESS.001
```

Password

```
x
```

The password is currently ignored by Seymour.

---

# Example

```
Pool

stratum+tcp://192.168.1.169:3336

Worker

bc1xxxxxxxxxxxxxxxxxxxxxxxx.001

Password

x
```

---

# Connect

Save the mining profile.

Enable the profile.

Within a few seconds the miner should establish a Stratum session.

---

# Verify Connection

Watch the Stratum log.

```bash
sudo journalctl \
-u seymour-pool-engine-stratum.service \
-f
```

Expected messages:

```
Stratum connection opened

authorized

JOB worker=...

mining.notify
```

---

# Verify Active Sessions

Current workers:

```sql
SELECT
worker_name,
connected_at,
difficulty
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL;
```

Example:

```
worker_name

bc1....001

difficulty

42
```

---

# Verify Shares

Recent submissions:

```sql
SELECT
worker_name,
accepted,
created_at
FROM seymour_engine.stratum_submissions
ORDER BY created_at DESC
LIMIT 20;
```

You should begin seeing accepted shares.

---

# Verify Native Statistics

Pool statistics:

```bash
curl \
http://127.0.0.1:8561/api/v1/statistics/overview?window=5m
```

Example:

```json
{
  "activeWorkers":2,
  "hashrate":14300000000000,
  "acceptedShares":523,
  "rejectedShares":0
}
```

---

Worker statistics:

```bash
curl \
http://127.0.0.1:8561/api/v1/statistics/workers
```

Expected:

```
workerName

hashrate

difficulty

lastShareAt

online=true
```

---

# Variable Difficulty

New workers begin at the minimum configured difficulty.

Example:

```
42
```

As the miner submits shares, Seymour automatically adjusts difficulty to reach the configured target share interval.

Recent VarDiff adjustments appear in the logs.

```
VARDIFF_JOB
```

Example:

```
42

↓

84

↓

168

↓

336
```

Each increase issues a new mining job at the updated difficulty while allowing previously issued jobs to complete.

---

# Session-Based Job Validation

Seymour validates submitted shares against the difficulty that was assigned when each job was issued.

This prevents a common Variable Difficulty failure where shares submitted for older jobs are incorrectly evaluated using a newer difficulty.

Current implementation includes:

- Per-session job tracking
- Historical job difficulty mapping
- Session validation
- Clean job issuance
- Duplicate share detection

These features significantly improve compatibility with ASIC firmware during rapid difficulty adjustments.

---

# Accepted Shares

Healthy miners should continuously submit accepted shares.

Typical example:

```
Accepted

523

Rejected

0
```

If rejection rates remain high after initial startup, consult the troubleshooting guide.

---

# Multiple Miners

Additional miners simply use unique worker names.

Examples:

```
wallet.001

wallet.002

wallet.003

wallet.004
```

Each worker receives its own:

- Session
- Variable Difficulty
- Statistics
- Hashrate
- Share accounting

---

# Disconnecting

When a miner disconnects, Seymour records:

- Disconnect time
- Final difficulty
- Total submissions
- Accepted shares
- Rejected shares

Historical statistics remain available for reporting.

---

# Troubleshooting

If no shares appear:

Verify:

- Bitcoin Core is synchronized.
- Stratum service is running.
- Firewall allows TCP 3336.
- Worker name is correct.
- Wallet address is valid.

Useful commands:

Current sessions:

```sql
SELECT *
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL;
```

Recent shares:

```sql
SELECT *
FROM seymour_engine.stratum_submissions
ORDER BY created_at DESC
LIMIT 20;
```

Stratum log:

```bash
sudo journalctl \
-u seymour-pool-engine-stratum.service \
-f
```

---

# Relationship to Other Documentation

This guide introduced the basic mining workflow.

The next guide explains how Seymour internally manages jobs, templates, share validation, and Variable Difficulty.

---

# Next Step

Continue with:

**06-STRATUM-ENGINE.md**
