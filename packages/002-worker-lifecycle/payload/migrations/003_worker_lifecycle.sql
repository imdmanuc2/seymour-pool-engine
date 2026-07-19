BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.workers (
    worker_id UUID PRIMARY KEY,
    provider_name TEXT NOT NULL,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    lifecycle_state TEXT NOT NULL DEFAULT 'unknown'
        CHECK (lifecycle_state IN ('active', 'offline', 'disabled', 'retired', 'unknown')),
    hashrate DOUBLE PRECISION NOT NULL DEFAULT 0,
    shares_per_second DOUBLE PRECISION NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    provider_observed_at TIMESTAMPTZ NOT NULL,
    last_sync_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    offline_since TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_workers_provider_identity
        UNIQUE (provider_name, pool_id, miner, worker)
);

CREATE INDEX IF NOT EXISTS idx_workers_provider_pool
    ON seymour_engine.workers (provider_name, pool_id);

CREATE INDEX IF NOT EXISTS idx_workers_lifecycle_state
    ON seymour_engine.workers (lifecycle_state, last_seen_at DESC);

CREATE INDEX IF NOT EXISTS idx_workers_last_seen
    ON seymour_engine.workers (last_seen_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('003_worker_lifecycle')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
