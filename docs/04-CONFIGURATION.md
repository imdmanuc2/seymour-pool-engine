# Seymour Pool Engine Configuration

**Version:** 1.0 (Development)

---

# Purpose

Seymour Pool Engine is configured primarily through environment variables.

This approach keeps configuration separate from application code, simplifies upgrades, and supports multiple deployment environments.

Configuration values are typically stored in:

```

/etc/seymour-pool-engine/engine.env

```

The systemd services load this file automatically during startup.

---

# Configuration Philosophy

Seymour follows several configuration principles:

- Configuration lives outside the application.
- Secrets are never committed to Git.
- Production and development environments use different configuration files.
- Environment variables override application defaults.
- All services share a common configuration source.

---

# Example engine.env

```env
####################################################
# Application
####################################################

SEYMOUR_ENVIRONMENT=production

SEYMOUR_LOG_LEVEL=INFO

####################################################
# API
####################################################

SEYMOUR_BIND_HOST=0.0.0.0

SEYMOUR_BIND_PORT=8561

####################################################
# Database
####################################################

SEYMOUR_DB_HOST=127.0.0.1

SEYMOUR_DB_PORT=5432

SEYMOUR_DB_NAME=seymour_pool_engine

SEYMOUR_DB_USER=seymour_engine

SEYMOUR_DB_PASSWORD=CHANGE_ME

####################################################
# Bitcoin Core
####################################################

SEYMOUR_RPC_HOST=127.0.0.1

SEYMOUR_RPC_PORT=8332

SEYMOUR_RPC_USERNAME=bitcoinrpc

SEYMOUR_RPC_PASSWORD=CHANGE_ME

####################################################
# Stratum
####################################################

SEYMOUR_STRATUM_HOST=0.0.0.0

SEYMOUR_STRATUM_PORT=3336

####################################################
# Variable Difficulty
####################################################

SEYMOUR_VARDIFF_ENABLED=true

SEYMOUR_VARDIFF_TARGET_SECONDS=15

SEYMOUR_VARDIFF_MIN_DIFFICULTY=42

SEYMOUR_VARDIFF_MAX_DIFFICULTY=500000000

####################################################
# Statistics
####################################################

SEYMOUR_STATISTICS_ENABLED=true

SEYMOUR_STATISTICS_REFRESH_SECONDS=30
```

---

# Application Settings

## Environment

```
SEYMOUR_ENVIRONMENT
```

Supported values:

- development
- testing
- production

---

## Logging

```
SEYMOUR_LOG_LEVEL
```

Supported values:

- DEBUG
- INFO
- WARNING
- ERROR

Production systems normally use:

```
INFO
```

---

# API Configuration

## Host

```
SEYMOUR_BIND_HOST
```

Usually:

```
0.0.0.0
```

---

## Port

```
SEYMOUR_BIND_PORT
```

Default:

```
8561
```

---

# Database Configuration

The PostgreSQL connection is controlled through:

```
SEYMOUR_DB_HOST

SEYMOUR_DB_PORT

SEYMOUR_DB_NAME

SEYMOUR_DB_USER

SEYMOUR_DB_PASSWORD
```

The database must be available before the API starts.

---

# Bitcoin Core RPC

These settings allow Seymour to communicate with Bitcoin Core.

```
SEYMOUR_RPC_HOST

SEYMOUR_RPC_PORT

SEYMOUR_RPC_USERNAME

SEYMOUR_RPC_PASSWORD
```

These credentials must match the values configured in:

```
bitcoin.conf
```

---

# Stratum Configuration

## Listen Address

```
SEYMOUR_STRATUM_HOST
```

Example:

```
0.0.0.0
```

---

## Port

```
SEYMOUR_STRATUM_PORT
```

Example:

```
3336
```

Miners connect to this port.

---

# Variable Difficulty

Variable Difficulty (VarDiff) automatically adjusts worker difficulty to maintain a target share submission rate.

Current production behavior:

- Session-bound job difficulty
- Per-job difficulty tracking
- Historical difficulty retention
- Clean job issuance after retargeting

Primary settings:

```
SEYMOUR_VARDIFF_ENABLED

SEYMOUR_VARDIFF_TARGET_SECONDS

SEYMOUR_VARDIFF_MIN_DIFFICULTY

SEYMOUR_VARDIFF_MAX_DIFFICULTY
```

---

# Statistics

Native statistics calculate:

- Pool hashrate
- Worker hashrate
- Active workers
- Accepted shares
- Rejected shares
- Share efficiency
- Rejection rate

Configuration:

```
SEYMOUR_STATISTICS_ENABLED

SEYMOUR_STATISTICS_REFRESH_SECONDS
```

---

# Restarting Services

After changing configuration:

Restart the API.

```bash
sudo systemctl restart \
seymour-pool-engine-api
```

Restart Stratum.

```bash
sudo systemctl restart \
seymour-pool-engine-stratum
```

Verify services.

```bash
sudo systemctl status \
seymour-pool-engine-api
```

```bash
sudo systemctl status \
seymour-pool-engine-stratum
```

---

# Verify Configuration

API health:

```bash
curl \
http://127.0.0.1:8561/api/v1/health
```

Statistics:

```bash
curl \
http://127.0.0.1:8561/api/v1/statistics/overview
```

Workers:

```bash
curl \
http://127.0.0.1:8561/api/v1/statistics/workers
```

---

# Best Practices

- Never store passwords in source control.
- Use separate configuration for development and production.
- Keep database credentials private.
- Restrict RPC access to trusted systems.
- Restart services after configuration changes.
- Verify health endpoints after every change.

---

# Common Problems

## API cannot connect to PostgreSQL

Verify:

- PostgreSQL is running.
- Database credentials are correct.
- Firewall rules allow local connections.

---

## RPC failures

Verify:

- Bitcoin Core is synchronized.
- RPC username and password match.
- RPC port is reachable.

---

## Miners cannot connect

Verify:

- Stratum service is running.
- Port 3336 is open.
- Firewall allows incoming connections.
- Worker credentials are correct.

---

# Relationship to Other Documentation

This document explains how Seymour is configured.

Operational procedures are covered later in:

- 07-OPERATIONS.md
- 09-SECURITY.md
- 10-TROUBLESHOOTING.md

---

# Next Step

Continue with:

**05-FIRST-MINER.md**

The next guide walks through connecting your first ASIC miner to Seymour Pool Engine and verifying successful share submission.
