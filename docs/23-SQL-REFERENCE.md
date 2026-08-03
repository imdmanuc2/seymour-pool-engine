# SQL Reference

**Document:** 23-SQL-REFERENCE.md

**Version:** 1.0 (Development)

---

# Purpose

This document provides commonly used SQL queries for administering, troubleshooting, and monitoring the Seymour Pool Engine database.

These queries are intended to be read-only unless otherwise noted.

---

# Database

Default database

```
seymour_pool_engine
```

Schema

```
seymour_engine
```

---

# Connect

```bash
sudo -u postgres psql \
    -d seymour_pool_engine
```

---

# Current Time

```sql
SELECT NOW();
```

---

# Current Sessions

```sql
SELECT
    session_id,
    worker_name,
    connected_at,
    disconnected_at
FROM seymour_engine.stratum_sessions
ORDER BY connected_at DESC;
```

---

# Active Workers

```sql
SELECT
    worker_name,
    session_id,
    connected_at
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL
ORDER BY connected_at DESC;
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
LIMIT 20;
```

---

# Recent Shares

```sql
SELECT
    created_at,
    worker_name,
    accepted,
    reject_reason
FROM seymour_engine.stratum_submissions
ORDER BY created_at DESC
LIMIT 50;
```

---

# Share Counts

```sql
SELECT
    accepted,
    COUNT(*)
FROM seymour_engine.stratum_submissions
GROUP BY accepted;
```

---

# Reject Reasons

```sql
SELECT
    reject_reason,
    COUNT(*)
FROM seymour_engine.stratum_submissions
WHERE accepted = FALSE
GROUP BY reject_reason
ORDER BY COUNT(*) DESC;
```

---

# Worker Statistics

```sql
SELECT
    worker_name,
    COUNT(*) total,
    COUNT(*) FILTER (WHERE accepted) accepted,
    COUNT(*) FILTER (WHERE NOT accepted) rejected
FROM seymour_engine.stratum_submissions
GROUP BY worker_name
ORDER BY worker_name;
```

---

# Current Session Health

```sql
WITH current_sessions AS (
    SELECT DISTINCT ON (worker_name)
        session_id,
        worker_name
    FROM seymour_engine.stratum_sessions
    WHERE disconnected_at IS NULL
    ORDER BY worker_name, connected_at DESC
)
SELECT
    c.worker_name,
    COUNT(s.*) total,
    COUNT(*) FILTER (WHERE s.accepted) accepted,
    COUNT(*) FILTER (WHERE NOT s.accepted) rejected
FROM current_sessions c
LEFT JOIN seymour_engine.stratum_submissions s
ON s.session_id = c.session_id
GROUP BY c.worker_name;
```

---

# Difficulty History

```sql
SELECT
    created_at,
    worker_name,
    old_difficulty,
    new_difficulty,
    observed_share_seconds,
    reason
FROM seymour_engine.stratum_difficulty_history
ORDER BY created_at DESC
LIMIT 50;
```

---

# Latest Block Templates

```sql
SELECT
    template_height,
    previous_block_hash,
    created_at
FROM seymour_engine.block_templates
ORDER BY created_at DESC
LIMIT 20;
```

---

# Pool Statistics Snapshot

```sql
SELECT *
FROM seymour_engine.native_statistics_snapshots
ORDER BY calculated_at DESC
LIMIT 20;
```

---

# Workers Without Activity

```sql
SELECT
    worker_name,
    connected_at
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL
AND last_activity_at < NOW() - INTERVAL '5 minutes';
```

---

# Highest Difficulty Shares

```sql
SELECT
    worker_name,
    share_difficulty,
    created_at
FROM seymour_engine.stratum_submissions
WHERE accepted
ORDER BY share_difficulty DESC
LIMIT 25;
```

---

# Duplicate Share Detection

```sql
SELECT
    submission_fingerprint,
    COUNT(*)
FROM seymour_engine.stratum_submissions
GROUP BY submission_fingerprint
HAVING COUNT(*) > 1;
```

---

# Session Timeline

```sql
SELECT
    worker_name,
    connected_at,
    disconnected_at
FROM seymour_engine.stratum_sessions
ORDER BY connected_at DESC;
```

---

# Database Size

```sql
SELECT
    pg_size_pretty(
        pg_database_size('seymour_pool_engine')
    );
```

---

# Largest Tables

```sql
SELECT
    relname,
    pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

---

# Index Usage

```sql
SELECT
    relname,
    idx_scan,
    seq_scan
FROM pg_stat_user_tables
ORDER BY idx_scan DESC;
```

---

# Long Running Queries

```sql
SELECT
    pid,
    now() - query_start duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;
```

---

# Vacuum Statistics

```sql
SELECT
    relname,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables;
```

---

# Version Information

```sql
SELECT version();
```

---

# Useful psql Commands

List tables

```
\\dt
```

Describe table

```
\\d table_name
```

List indexes

```
\\di
```

List schemas

```
\\dn
```

Quit

```
\\q
```

---

# Best Practices

- Prefer read-only queries during production troubleshooting.
- Use indexes whenever possible.
- Avoid long-running table scans on production systems.
- Run maintenance during scheduled windows.
- Verify query plans before introducing new reports.

---

# Summary

This reference provides a collection of commonly used SQL queries for operating and troubleshooting the Seymour Pool Engine. It should be expanded as new features and database objects are introduced while maintaining compatibility with the Version 1.x schema.

---

# Next Step

Continue with:

**24-CONFIGURATION-REFERENCE.md**
