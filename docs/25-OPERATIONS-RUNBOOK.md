# Operations Runbook

**Document:** 25-OPERATIONS-RUNBOOK.md

**Version:** 1.0 (Development)

---

# Purpose

This runbook provides the standard operational procedures for managing a Seymour Pool Engine deployment.

It is intended for production administrators responsible for monitoring, maintaining, and recovering the platform.

---

# Operational Goals

Production operations should prioritize:

- Continuous mining
- Accurate statistics
- Stable Stratum service
- Reliable REST API
- Database integrity
- Minimal downtime

---

# Daily Health Check

Verify all core services.

```bash
sudo systemctl status seymour-pool-engine-api
sudo systemctl status seymour-pool-engine-stratum
sudo systemctl status postgresql
```

All services should report:

```
active (running)
```

---

# Verify REST API

```bash
curl \
http://127.0.0.1:8561/api/v1/health
```

Expected:

```json
{
    "status":"healthy"
}
```

---

# Verify Pool Statistics

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/overview?window=5m"
```

Confirm:

- Active workers
- Pool hashrate
- Accepted shares
- Zero unexpected rejects

---

# Verify Worker Statistics

```bash
curl \
"http://127.0.0.1:8561/api/v1/statistics/workers?window=5m"
```

Verify:

- Worker online
- Difficulty
- Hashrate
- Share activity

---

# Check Stratum Connections

```bash
ss -ltn
```

Confirm the configured Stratum port is listening.

---

# Monitor Live Logs

API

```bash
sudo journalctl -fu seymour-pool-engine-api
```

Stratum

```bash
sudo journalctl -fu seymour-pool-engine-stratum
```

---

# PostgreSQL Health

```bash
sudo systemctl status postgresql
```

Verify database connectivity.

```bash
sudo -u postgres psql \
-d seymour_pool_engine
```

---

# Confirm Active Workers

```sql
SELECT
worker_name,
connected_at
FROM seymour_engine.stratum_sessions
WHERE disconnected_at IS NULL;
```

---

# Verify Recent Shares

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

# Restart API

```bash
sudo systemctl restart \
seymour-pool-engine-api
```

Verify:

```bash
systemctl status
```

---

# Restart Stratum

```bash
sudo systemctl restart \
seymour-pool-engine-stratum
```

Watch miners reconnect.

---

# Planned Maintenance

Recommended sequence:

1. Notify users
2. Stop Stratum
3. Complete maintenance
4. Start Stratum
5. Verify workers reconnect
6. Verify statistics
7. Verify REST API

---

# Database Backup

Example

```bash
pg_dump \
seymour_pool_engine \
> backup.sql
```

Verify backups regularly.

---

# Database Restore

Example

```bash
psql \
seymour_pool_engine \
< backup.sql
```

Always test restores before production use.

---

# Software Updates

Recommended process:

1. Backup database
2. Backup configuration
3. Pull new source
4. Apply migrations
5. Restart services
6. Verify statistics
7. Verify miners reconnect

---

# Migration Verification

Confirm:

- Migration completed
- Tables exist
- Indexes exist
- API responds
- Shares continue flowing

---

# Worker Health

Healthy workers should show:

- Online
- Accepted shares
- Recent activity
- Stable hashrate
- Appropriate difficulty

---

# Pool Health

Healthy pool indicators:

- Active workers
- Increasing accepted shares
- Zero or low rejection rate
- Recent accepted share
- Stable hashrate

---

# Incident Response

When problems occur:

1. Preserve logs.
2. Record timestamps.
3. Verify services.
4. Verify PostgreSQL.
5. Verify Stratum.
6. Verify statistics.
7. Restore service.

---

# Performance Monitoring

Regularly monitor:

- CPU
- Memory
- Disk
- PostgreSQL
- Network
- API latency
- Share throughput

---

# Security

Regularly verify:

- Environment file permissions
- PostgreSQL authentication
- RPC credentials
- SSH access
- Service accounts

---

# Recommended Maintenance Schedule

Daily

- Verify services
- Verify statistics
- Check logs

Weekly

- Backup database
- Review rejection rates
- Verify storage

Monthly

- Apply updates
- Review performance
- Test restore procedures

Quarterly

- Audit configuration
- Verify documentation
- Review operational procedures

---

# Nexus Integration

Verify that Nexus displays:

- Correct hashrate
- Correct worker count
- Current pool health
- Current worker health

Nexus should consume Seymour's REST API rather than querying the database directly for operational dashboards.

---

# Recovery Checklist

After any outage:

✓ API online

✓ Stratum online

✓ PostgreSQL online

✓ Workers connected

✓ Workers authorized

✓ Shares accepted

✓ Statistics updating

✓ Nexus synchronized

---

# Summary

This runbook provides the standard operating procedures for managing a Seymour Pool Engine deployment.

Following these procedures helps maintain reliable mining operations while minimizing downtime and simplifying incident recovery.

---

# Next Step

Continue with:

**26-CHANGELOG-GUIDE.md**
