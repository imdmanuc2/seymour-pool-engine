# Production Installation

**Version:** 1.0 (Development)

---

# Purpose

This guide walks through deploying Seymour Pool Engine on a clean Linux server for production use.

At the end of this guide, you will have:

- PostgreSQL installed and configured
- Bitcoin Core connected
- Seymour Pool Engine installed
- Native Stratum server running
- REST API running
- Systemd services configured
- A production-ready Bitcoin solo mining pool

Subsequent documents will cover configuration, miner onboarding, operations, backup, security, and troubleshooting.

---

# Supported Platform

Version 1.0 is developed and tested on:

- Debian 13 (Trixie)
- Ubuntu 24.04 LTS (expected compatible)
- Python 3.13+
- PostgreSQL 16+
- Bitcoin Core 29+

---

# Hardware Recommendations

## Small Deployment

- 2 CPU cores
- 4 GB RAM
- 50 GB SSD

Suitable for:

- Home mining
- Solo mining
- Development

---

## Recommended Production

- 4+ CPU cores
- 8 GB RAM
- SSD storage
- Reliable network connection

---

# Installation Overview

The installation process consists of:

1. Prepare Linux
2. Install PostgreSQL
3. Install Bitcoin Core
4. Clone Seymour Pool Engine
5. Create Python environment
6. Configure environment
7. Run database migrations
8. Install systemd services
9. Verify operation

---

# Step 1 — Prepare Linux

Update the operating system.

```bash
sudo apt update
sudo apt upgrade -y
```

Install required packages.

```bash
sudo apt install \
git \
python3 \
python3-venv \
python3-pip \
build-essential \
curl \
jq
```

---

# Step 2 — Install PostgreSQL

Continue with:

**02-POSTGRESQL.md**

---

# Step 3 — Install Bitcoin Core

Continue with:

**03-BITCOIN-CORE.md**

---

# Step 4 — Clone Seymour

```bash
git clone https://github.com/imdmanuc2/seymour-pool-engine.git

cd seymour-pool-engine
```

---

# Step 5 — Create Virtual Environment

```bash
python3 -m venv .venv

source .venv/bin/activate

pip install -e .
```

---

# Step 6 — Configure Environment

Copy the example configuration.

```bash
cp .env.example .env
```

Complete the configuration using:

**04-CONFIGURATION.md**

---

# Step 7 — Database

Run the migration scripts.

(Migration commands will evolve as Version 1.0 progresses.)

---

# Step 8 — Install Services

Install:

- seymour-pool-engine-api.service
- seymour-pool-engine-stratum.service

Enable both services.

```bash
sudo systemctl enable seymour-pool-engine-api

sudo systemctl enable seymour-pool-engine-stratum
```

Start both services.

```bash
sudo systemctl start seymour-pool-engine-api

sudo systemctl start seymour-pool-engine-stratum
```

---

# Step 9 — Verify

Confirm services are running.

```bash
sudo systemctl status seymour-pool-engine-api

sudo systemctl status seymour-pool-engine-stratum
```

Verify the API.

```bash
curl http://127.0.0.1:8561/api/v1/health
```

Verify the Stratum listener.

```bash
ss -ltn | grep 3336
```

---

# Next Steps

Continue with:

- 02-POSTGRESQL.md
- 03-BITCOIN-CORE.md
- 04-CONFIGURATION.md
- 05-FIRST-MINER.md

Once complete, your first ASIC miner can connect to Seymour Pool Engine.
