# PostgreSQL Configuration

**Version:** 1.0 (Development)

---

# Purpose

Seymour Pool Engine uses PostgreSQL as its authoritative data store.

All persistent mining state is stored in PostgreSQL including:

- Mining sessions
- Workers
- Jobs
- Share submissions
- Variable Difficulty history
- Native statistics
- Database migrations

Unlike legacy mining software, Seymour treats PostgreSQL as a core component rather than optional storage.

---

# Why PostgreSQL?

The engine requires:

- ACID transactions
- High write throughput
- Historical auditing
- Complex analytics
- Native indexing
- Reliable backups

PostgreSQL provides these capabilities while remaining widely available on Linux distributions.

---

# Installation

Update package indexes.

```bash
sudo apt update
```

Install PostgreSQL.

```bash
sudo apt install postgresql
```

Enable automatic startup.

```bash
sudo systemctl enable postgresql

sudo systemctl start postgresql
```

Verify installation.

```bash
systemctl status postgresql
```

---

# Create Database

Switch to the postgres user.

```bash
sudo -u postgres psql
```

Create the application user.

```sql
CREATE USER seymour_engine
WITH PASSWORD 'CHANGE_ME';
```

Create the production database.

```sql
CREATE DATABASE seymour_pool_engine
OWNER seymour_engine;
```

Grant privileges.

```sql
GRANT ALL PRIVILEGES
ON DATABASE seymour_pool_engine
TO seymour_engine;
```

Exit PostgreSQL.

```sql
\q
```

---

# Verify Connectivity

Test the connection.

```bash
psql \
-h localhost \
-U seymour_engine \
-d seymour_pool_engine
```

You should receive a PostgreSQL prompt.

---

# Database Schema

The database consists of multiple logical areas.

## Sessions

Stores:

- Connected miners
- Authorization state
- Difficulty
- Connection metadata

---

## Jobs

Stores every mining job issued to miners.

Jobs remain available for deterministic share validation.

---

## Share Submissions

Stores every validated share.

Each record includes:

- Worker
- Job
- Timestamp
- Accepted / rejected
- Share difficulty
- Block candidate flag
- Share hash

---

## Difficulty History

Records every VarDiff adjustment.

Useful for:

- Diagnostics
- Performance tuning
- Historical analysis

---

## Statistics

Stores calculated snapshots including:

- Pool hashrate
- Worker hashrate
- Share counts
- Efficiency
- Rejection rates

---

# Migrations

Seymour manages schema evolution using versioned migrations.

Example:

```
001_initial.sql

002_worker_lifecycle.sql

...

026_native_hashrate_statistics.sql
```

Each migration executes exactly once.

Applied migrations are tracked in the database.

---

# Backup

Create a backup.

```bash
pg_dump \
-U seymour_engine \
-d seymour_pool_engine \
> seymour-backup.sql
```

Restore.

```bash
psql \
-U seymour_engine \
-d seymour_pool_engine \
< seymour-backup.sql
```

For production backup strategies, see:

**08-BACKUP-RESTORE.md**

---

# Performance

Recommended production settings:

- SSD storage
- WAL enabled
- Autovacuum enabled
- Daily backups
- Routine VACUUM ANALYZE

Large pools may benefit from additional tuning as worker count increases.

---

# Troubleshooting

List databases.

```bash
psql -l
```

List tables.

```bash
\dt
```

List schemas.

```bash
\dn
```

View active connections.

```sql
SELECT *
FROM pg_stat_activity;
```

Database size.

```sql
SELECT pg_size_pretty(
    pg_database_size('seymour_pool_engine')
);
```

---

# Next Step

Continue with:

**03-BITCOIN-CORE.md**

The next document configures the Bitcoin node that provides block templates and accepts completed block submissions from Seymour Pool Engine.
