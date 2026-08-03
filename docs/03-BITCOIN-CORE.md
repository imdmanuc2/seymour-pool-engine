# Bitcoin Core Configuration

**Version:** 1.0 (Development)

---

# Purpose

Seymour Pool Engine does not generate blocks independently.

Instead, it relies on a fully synchronized Bitcoin Core node to:

- Maintain the blockchain
- Validate consensus rules
- Build block templates
- Submit solved blocks
- Broadcast accepted blocks to the Bitcoin network

Bitcoin Core is the authoritative blockchain source used by Seymour.

---

# Requirements

Recommended minimum hardware:

| Component | Recommended |
|-----------|-------------|
| CPU | Quad Core |
| Memory | 8 GB |
| Storage | 2 TB NVMe SSD |
| Network | Stable broadband |

Production systems should use SSD storage.

---

# Install Bitcoin Core

Download the official Bitcoin Core release.

Extract the archive.

Install the binaries.

Example:

```bash
tar -xzf bitcoin-*.tar.gz

sudo install -m 0755 -o root -g root \
bin/* \
/usr/local/bin/
```

Verify installation.

```bash
bitcoind --version
```

---

# Data Directory

Create the Bitcoin data directory.

```bash
mkdir -p ~/.bitcoin
```

---

# bitcoin.conf

Create:

```
~/.bitcoin/bitcoin.conf
```

Example configuration:

```ini
server=1

daemon=1

txindex=1

rpcbind=127.0.0.1

rpcallowip=127.0.0.1

rpcuser=CHANGE_ME

rpcpassword=CHANGE_ME

rpcport=8332

listen=1

prune=0
```

---

# Why txindex?

Seymour performs blockchain analysis and diagnostics.

Running with:

```
txindex=1
```

provides complete transaction indexing and improves operational tooling.

---

# Start Bitcoin Core

```bash
bitcoind
```

or using systemd:

```bash
sudo systemctl start bitcoind
```

---

# Synchronization

Initial synchronization may require:

- several hours
- or several days

depending on hardware and internet speed.

Verify progress.

```bash
bitcoin-cli getblockchaininfo
```

Example:

```json
{
    "blocks": 912345,
    "headers": 912345,
    "verificationprogress": 0.999998
}
```

Mining should not begin until synchronization reaches 100%.

---

# RPC Verification

Test RPC connectivity.

```bash
bitcoin-cli getblockchaininfo
```

Test block template generation.

```bash
bitcoin-cli getblocktemplate
```

A valid JSON response confirms Seymour can request mining work.

---

# Seymour Integration

Configure Seymour's environment variables.

Example:

```env
SEYMOUR_RPC_HOST=127.0.0.1

SEYMOUR_RPC_PORT=8332

SEYMOUR_RPC_USERNAME=CHANGE_ME

SEYMOUR_RPC_PASSWORD=CHANGE_ME
```

Restart the API after changing configuration.

```bash
sudo systemctl restart \
seymour-pool-engine-api
```

---

# Health Checks

Verify Bitcoin Core.

```bash
bitcoin-cli getnetworkinfo
```

Verify synchronization.

```bash
bitcoin-cli getblockchaininfo
```

Verify mining templates.

```bash
bitcoin-cli getblocktemplate
```

Verify Seymour.

```bash
curl \
http://127.0.0.1:8561/api/v1/health
```

---

# Security

Production recommendations:

- Never expose RPC to the Internet.
- Restrict RPC to localhost or trusted management networks.
- Use strong RPC credentials.
- Protect wallet files with regular backups.
- Keep Bitcoin Core updated.

---

# Troubleshooting

Check synchronization.

```bash
bitcoin-cli getblockchaininfo
```

Check peer count.

```bash
bitcoin-cli getconnectioncount
```

Check node uptime.

```bash
bitcoin-cli uptime
```

View recent logs.

```bash
tail -f ~/.bitcoin/debug.log
```

---

# Relationship to Seymour

Bitcoin Core is responsible for:

- Blockchain validation
- Block template generation
- Network communication
- Block submission

Seymour Pool Engine is responsible for:

- Stratum protocol
- Miner management
- Share validation
- Variable difficulty
- Statistics
- Pool operations

The two systems work together but have clearly separated responsibilities.

---

# Next Step

Continue with:

**04-CONFIGURATION.md**

The next document explains every Seymour Pool Engine configuration option, environment variable, and runtime setting.
