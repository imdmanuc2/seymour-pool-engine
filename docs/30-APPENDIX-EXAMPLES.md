# Appendix - Examples

**Document:** 30-APPENDIX-EXAMPLES.md

**Version:** 1.0 (Development)

---

# Purpose

This appendix provides practical examples of common Seymour Pool Engine operations.

The examples are intended to accelerate development, simplify troubleshooting, and demonstrate common administrative tasks.

---

# API Examples

## Health Check

```bash
curl \
http://127.0.0.1:8561/api/v1/health
```

---

## Pool Statistics

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=5m"
```

---

## Worker Statistics

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/workers?window=5m"
```

---

## Pretty Printed JSON

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=15m" \
| python3 -m json.tool
```

---

# SQL Examples

## Current Sessions

```sql
SELECT
    worker_name,
    connected_at
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL;
```

---

## Latest Shares

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

## Acceptance Rate

```sql
SELECT
    worker_name,
    COUNT(*) total,
    COUNT(*) FILTER (WHERE accepted) accepted,
    ROUND(
        100.0 *
        COUNT(*) FILTER (WHERE accepted)
        / COUNT(*),
        2
    ) accepted_percent
FROM seymour_engine.stratum_submissions
GROUP BY worker_name;
```

---

## Recent Jobs

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

# Service Management

## Start API

```bash
sudo systemctl start \
seymour-pool-engine-api
```

---

## Stop API

```bash
sudo systemctl stop \
seymour-pool-engine-api
```

---

## Restart API

```bash
sudo systemctl restart \
seymour-pool-engine-api
```

---

## Restart Stratum

```bash
sudo systemctl restart \
seymour-pool-engine-stratum
```

---

## View Status

```bash
systemctl status \
seymour-pool-engine-api

systemctl status \
seymour-pool-engine-stratum
```

---

# Logging

## Live API Log

```bash
journalctl -fu \
seymour-pool-engine-api
```

---

## Live Stratum Log

```bash
journalctl -fu \
seymour-pool-engine-stratum
```

---

## Search VarDiff Events

```bash
journalctl \
-u seymour-pool-engine-stratum \
| grep VARDIFF_JOB
```

---

## Search Authorization Events

```bash
journalctl \
-u seymour-pool-engine-stratum \
| grep authorized
```

---

## Search Rejected Shares

```bash
journalctl \
-u seymour-pool-engine-stratum \
| grep rejected
```

---

# PostgreSQL

## Connect

```bash
sudo -u postgres psql \
-d seymour_pool_engine
```

---

## Database Size

```sql
SELECT
pg_size_pretty(
pg_database_size(
'seymour_pool_engine'
));
```

---

## Version

```sql
SELECT version();
```

---

# Development

## Format

```bash
ruff format
```

---

## Lint

```bash
ruff check
```

---

## Run Tests

```bash
pytest
```

---

## Specific Test

```bash
pytest \
tests/test_stratum_dispatcher.py
```

---

# Git

## Status

```bash
git status
```

---

## Pull

```bash
git pull
```

---

## Commit

```bash
git commit \
-m "Describe change"
```

---

## Push

```bash
git push origin develop
```

---

# Common Operational Workflow

```
Edit Code

↓

Format

↓

Lint

↓

Run Tests

↓

Commit

↓

Push

↓

Deploy

↓

Restart Services

↓

Verify API

↓

Verify Statistics

↓

Verify Workers
```

---

# Production Verification

After deployment verify:

✓ API healthy

✓ Stratum listening

✓ PostgreSQL online

✓ Workers connected

✓ Workers authorized

✓ Shares accepted

✓ Statistics updating

✓ Nexus receiving data

---

# Example Health Verification

```bash
curl http://127.0.0.1:8561/api/v1/health

curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=5m"

sudo systemctl status \
seymour-pool-engine-api

sudo systemctl status \
seymour-pool-engine-stratum
```

---

# Related Documentation

00 – Start Here

Architecture

Database Schema

Development Guide

REST API Reference

Configuration Reference

Operations Runbook

Troubleshooting

SQL Reference

---

# Summary

This appendix provides practical examples that can be copied directly into a terminal or development workflow. It complements the reference documentation by demonstrating common operational, administrative, and development tasks used throughout the Seymour Pool Engine lifecycle.
