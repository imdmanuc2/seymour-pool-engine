# Troubleshooting

**Document:** 20-TROUBLESHOOTING.md

**Version:** 1.0 (Development)

---

# Purpose

This guide provides procedures for diagnosing and resolving common Seymour Pool Engine problems.

It is intended for operators, administrators, and developers responsible for maintaining a production Seymour deployment.

---

# Troubleshooting Philosophy

Troubleshooting should proceed from the outside inward.

```
Miners

↓

Network

↓

Stratum

↓

Share Validation

↓

Database

↓

REST API

↓

Nexus
```

Never assume the source of the problem.

Always verify each layer independently.

---

# Verify Services

Check all Seymour services.

```bash
sudo systemctl status seymour-pool-engine-api
```

```bash
sudo systemctl status seymour-pool-engine-stratum
```

Expected:

```
active (running)
```

---

# View Live Logs

API

```bash
sudo journalctl -fu seymour-pool-engine-api
```

Stratum

```bash
sudo journalctl -fu seymour-pool-engine-stratum
```

---

# API Health

Verify the API responds.

```bash
curl http://127.0.0.1:8561/api/v1/health
```

Expected response:

```json
{
  "status":"healthy"
}
```

---

# Statistics

Pool overview

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=5m"
```

Workers

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/workers?window=5m"
```

---

# No Connected Workers

Possible causes

- wrong port
- firewall
- authorization failure
- miner offline
- DNS failure

Check

```bash
ss -ltn
```

Confirm Stratum is listening.

---

# Miner Cannot Connect

Verify

- IP address
- port
- wallet
- worker name
- firewall
- routing

Look for

```
connection opened
```

in the Stratum log.

---

# Worker Never Authorizes

Check

```
mining.authorize
```

messages.

Logs should show

```
authorized
```

---

# Shares Never Arrive

Possible causes

- miner idle
- incorrect difficulty
- firmware issue
- networking
- stale jobs

Look for

```
mining.submit
```

activity.

---

# High Reject Rate

Check

- stale jobs
- duplicate shares
- incorrect difficulty
- VarDiff
- firmware compatibility

Query

```sql
SELECT
accepted,
reject_reason,
COUNT(*)
FROM seymour_engine.stratum_submissions
GROUP BY
accepted,
reject_reason;
```

---

# Difficulty Problems

Inspect

```
stratum_difficulty_history
```

Example

```sql
SELECT *

FROM seymour_engine.stratum_difficulty_history

ORDER BY created_at DESC

LIMIT 20;
```

---

# Hashrate Looks Wrong

Remember

Hashrate is estimated.

Small windows fluctuate naturally.

Compare

```
5m

15m

1h
```

before assuming a problem exists.

---

# Worker Shows Offline

Verify

```
lastActivityAt
```

and

```
online
```

Workers disconnected several hours ago remain in history.

They should not count as active workers.

---

# Pool Shows Zero Hashrate

Check

- accepted shares
- current sessions
- statistics window
- API restart
- PostgreSQL

---

# Database Connectivity

Verify

```bash
sudo systemctl status postgresql
```

Connect

```bash
psql
```

Check

```sql
SELECT NOW();
```

---

# Recent Shares

```sql
SELECT

worker_name,

accepted,

created_at

FROM seymour_engine.stratum_submissions

ORDER BY created_at DESC

LIMIT 20;
```

---

# Active Sessions

```sql
SELECT

worker_name,

connected_at,

disconnected_at

FROM seymour_engine.stratum_sessions;
```

---

# Recent Jobs

```sql
SELECT

job_id,

template_height,

created_at

FROM seymour_engine.stratum_jobs

ORDER BY created_at DESC

LIMIT 10;
```

---

# REST API Problems

Verify

```
systemctl status
```

then

```
curl
```

before debugging Nexus.

---

# Nexus Shows Incorrect Data

Verify

1. Seymour API
2. Native Statistics
3. Network connectivity
4. CMDB synchronization
5. Cached browser data

The Pool Engine owns mining truth.

Nexus displays that truth.

---

# Version Rolling Issues

Check

- negotiated mask
- submitted version bits
- firmware support

Look for

```
invalid-version
```

errors.

---

# Block Submission Problems

Verify

- Bitcoin Core reachable
- RPC authentication
- RPC permissions
- network synchronization

---

# Performance Problems

Inspect

- PostgreSQL
- CPU
- memory
- disk
- network

Long-running SQL queries should be investigated.

---

# Logging

Useful commands

```bash
journalctl
```

```bash
tail
```

```bash
grep
```

---

# Debug Checklist

✓ API running

✓ Stratum running

✓ PostgreSQL running

✓ Workers connected

✓ Workers authorized

✓ Jobs issued

✓ Shares submitted

✓ Shares accepted

✓ Statistics updating

✓ Nexus displaying data

---

# Common Production Issues

| Symptom | Likely Cause |
|----------|--------------|
| No workers | Network or configuration |
| Workers connect but never authorize | Credentials |
| Workers authorize but never submit | Miner issue |
| High rejects | Difficulty or stale jobs |
| Zero hashrate | No accepted shares |
| API unavailable | Service stopped |
| Statistics frozen | Database or service failure |
| Nexus incorrect | Synchronization issue |

---

# Collecting Support Information

When requesting assistance include

- Seymour version
- Git commit
- Python version
- PostgreSQL version
- API logs
- Stratum logs
- Recent SQL output
- Current statistics
- Current worker list

Providing this information significantly reduces troubleshooting time.

---

# Best Practices

- Keep software updated.
- Monitor logs regularly.
- Back up the database.
- Document configuration changes.
- Test changes before production deployment.
- Verify statistics after upgrades.

---

# Summary

Most Seymour issues can be isolated by validating each layer independently, beginning with miner connectivity and ending with API responses.

Following the procedures in this guide provides a consistent approach to diagnosing production problems while preserving reliable mining operations.

---

# Next Step

Continue with:

**19-REST-API-REFERENCE.md**
