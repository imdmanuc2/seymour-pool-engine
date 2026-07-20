BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.blocks (
    block_id UUID PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_block_key TEXT NOT NULL,
    pool_id TEXT NOT NULL,
    block_height BIGINT NOT NULL,
    block_hash TEXT,
    status TEXT NOT NULL DEFAULT 'candidate',
    confirmations INTEGER NOT NULL DEFAULT 0,
    network_difficulty DOUBLE PRECISION,
    reward NUMERIC(28, 12),
    miner TEXT,
    worker TEXT NOT NULL DEFAULT '',
    share_id UUID REFERENCES seymour_engine.shares(share_id) ON DELETE SET NULL,
    found_at TIMESTAMPTZ NOT NULL,
    confirmed_at TIMESTAMPTZ,
    orphaned_at TIMESTAMPTZ,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_blocks_provider_key UNIQUE (provider_name, provider_block_key),
    CONSTRAINT ck_blocks_status CHECK (
        status IN ('candidate', 'immature', 'confirmed', 'orphaned')
    ),
    CONSTRAINT ck_blocks_confirmations CHECK (confirmations >= 0)
);

CREATE INDEX IF NOT EXISTS idx_blocks_pool_found
    ON seymour_engine.blocks (pool_id, found_at DESC);

CREATE INDEX IF NOT EXISTS idx_blocks_status_updated
    ON seymour_engine.blocks (status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_blocks_height
    ON seymour_engine.blocks (block_height DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.block_events (
    event_id UUID PRIMARY KEY,
    block_id UUID NOT NULL REFERENCES seymour_engine.blocks(block_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    confirmations INTEGER NOT NULL DEFAULT 0,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT ck_block_events_type CHECK (
        event_type IN ('discovered', 'status_changed', 'confirmation_updated')
    )
);

CREATE INDEX IF NOT EXISTS idx_block_events_block_time
    ON seymour_engine.block_events (block_id, occurred_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('006_block_lifecycle')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
