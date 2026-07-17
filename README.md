# Seymour Pool Engine

Seymour Pool Engine is the management, orchestration, health, operations,
and integration layer for Seymour Pool.

It exposes a stable API to Nexus Command Center while abstracting the
underlying mining engine, PostgreSQL databases, blockchain nodes, Stratum
listeners, and host services.

## Architecture

```text
Nexus Command Center
        |
        v
Seymour Pool Engine API
        |
        +-- Seymour Engine PostgreSQL database
        +-- MiningCore PostgreSQL database
        +-- MiningCore API
        +-- Blockchain RPC
        +-- Stratum listeners
        +-- systemd services
