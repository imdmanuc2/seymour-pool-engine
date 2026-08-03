# Configuration Reference

**Document:** 24-CONFIGURATION-REFERENCE.md

**Version:** 1.0 (Development)

---

# Purpose

This document describes the configuration options used by the Seymour Pool Engine.

Configuration controls how the engine communicates with miners, Bitcoin Core, PostgreSQL, Nexus Command Center, and other platform services.

---

# Configuration Philosophy

The Seymour Pool Engine follows several configuration principles.

- Environment-driven configuration
- No secrets stored in source code
- Production-safe defaults where practical
- Explicit configuration over hidden behavior
- One configuration source per deployment

---

# Configuration Files

Typical production layout:

```
/etc/seymour-pool-engine/
    engine.env
```

Development:

```
.env
```

---

# Environment Variables

Configuration is loaded from environment variables.

Typical startup:

```bash
source .env
```

or

```bash
EnvironmentFile=/etc/seymour-pool-engine/engine.env
```

within the systemd service.

---

# API Configuration

Typical options include:

```
SEYMOUR_API_HOST

SEYMOUR_API_PORT

SEYMOUR_API_LOG_LEVEL
```

These control the REST API listener.

---

# Stratum Configuration

Typical variables include:

```
SEYMOUR_STRATUM_HOST

SEYMOUR_STRATUM_PORT

SEYMOUR_STRATUM_LOG_LEVEL
```

These configure the mining server.

---

# Database Configuration

Typical variables include:

```
SEYMOUR_DB_HOST

SEYMOUR_DB_PORT

SEYMOUR_DB_NAME

SEYMOUR_DB_USER

SEYMOUR_DB_PASSWORD
```

The engine requires PostgreSQL for persistent storage.

---

# Bitcoin RPC

Bitcoin node communication typically requires:

```
SEYMOUR_RPC_HOST

SEYMOUR_RPC_PORT

SEYMOUR_RPC_USERNAME

SEYMOUR_RPC_PASSWORD
```

RPC credentials should never be committed to source control.

---

# Logging

Typical options include:

```
INFO

WARNING

ERROR

DEBUG
```

Production systems generally use:

```
INFO
```

Development often uses:

```
DEBUG
```

---

# Variable Difficulty

Typical configuration options include:

```
Target share interval

Minimum difficulty

Maximum difficulty

Adjustment interval
```

Proper VarDiff configuration is essential for efficient mining.

---

# Statistics

Native Statistics may expose configurable windows such as:

```
1 minute

5 minutes

15 minutes

1 hour
```

Future releases may support longer historical windows.

---

# Timeouts

Common timeout settings include:

- Idle session timeout
- RPC timeout
- Database timeout
- API request timeout

Timeout values should balance responsiveness with stability.

---

# systemd

Typical API service:

```
seymour-pool-engine-api.service
```

Typical Stratum service:

```
seymour-pool-engine-stratum.service
```

Environment files are referenced from the service definitions.

---

# Security

Recommendations:

- Restrict permissions on environment files.
- Protect RPC credentials.
- Do not expose Stratum unnecessarily.
- Restrict API access to trusted networks.
- Rotate secrets periodically.

---

# Production Recommendations

Use dedicated service accounts.

Separate:

- PostgreSQL
- Bitcoin Core
- Seymour
- Nexus

whenever practical.

---

# Configuration Validation

After changing configuration:

1. Restart the affected service.
2. Verify systemd status.
3. Confirm logs show successful startup.
4. Test the REST API.
5. Verify Stratum connectivity.
6. Confirm miners reconnect successfully.

---

# Backup

Back up:

- Environment files
- systemd service files
- Database
- Migrations

Configuration should be version controlled where secrets are excluded.

---

# Troubleshooting

If configuration changes fail:

- Check environment variable names.
- Verify file permissions.
- Confirm service restart.
- Review startup logs.
- Validate database connectivity.
- Test Bitcoin RPC.

---

# Future Configuration

Future versions may introduce:

- Configuration profiles
- Hot reload
- Web-based configuration
- Secrets manager integration
- Distributed configuration

These features are outside the Version 1.0 scope.

---

# Summary

The Seymour Pool Engine uses a straightforward environment-based configuration model that supports secure production deployments while remaining easy to understand and automate.

---

# Next Step

Continue with:

**25-OPERATIONS-RUNBOOK.md**
