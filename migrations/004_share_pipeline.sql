BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.shares (
    share_id UUID PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_share_key TEXT NOT NULL,
    worker_id UUID REFERENCES seymour_engine.workers(worker_id) ON DELETE SET NULL,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    difficulty DOUBLE PRECISION NOT NULL DEFAULT 0,
    network_difficulty DOUBLE PRECISION,
    block_height BIGINT,
    ip_address TEXT,
    user_agent TEXT,
    provider_created_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_shares_provider_key UNIQUE (provider_name, provider_share_key)
);

CREATE INDEX IF NOT EXISTS idx_shares_pool_created
    ON seymour_engine.shares (pool_id, provider_created_at DESC);

CREATE INDEX IF NOT EXISTS idx_shares_worker_created
    ON seymour_engine.shares (worker_id, provider_created_at DESC);

CREATE INDEX IF NOT EXISTS idx_shares_provider_created
    ON seymour_engine.shares (provider_name, provider_created_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('004_share_pipeline')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
