BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.payout_batches (
    payout_batch_id UUID PRIMARY KEY,
    batch_key TEXT NOT NULL UNIQUE,
    pool_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    source_wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'draft',
    minimum_payout NUMERIC(28, 12) NOT NULL DEFAULT 0,
    total_amount NUMERIC(28, 12) NOT NULL DEFAULT 0,
    item_count INTEGER NOT NULL DEFAULT 0,
    transaction_id TEXT,
    requested_by TEXT NOT NULL,
    approved_by TEXT,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT ck_payout_batch_status CHECK (
        status IN ('draft', 'approved', 'processing', 'completed', 'failed', 'cancelled')
    ),
    CONSTRAINT ck_payout_batch_amounts CHECK (
        minimum_payout >= 0 AND total_amount >= 0 AND item_count >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_payout_batches_pool_status
    ON seymour_engine.payout_batches (pool_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.payout_items (
    payout_item_id UUID PRIMARY KEY,
    payout_batch_id UUID NOT NULL REFERENCES seymour_engine.payout_batches(payout_batch_id) ON DELETE CASCADE,
    worker_id UUID REFERENCES seymour_engine.workers(worker_id) ON DELETE SET NULL,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    destination_address TEXT NOT NULL,
    amount NUMERIC(28, 12) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    transaction_id TEXT,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_payout_item_identity UNIQUE (payout_batch_id, pool_id, miner, worker),
    CONSTRAINT ck_payout_item_status CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
    ),
    CONSTRAINT ck_payout_item_amount CHECK (amount > 0)
);

CREATE INDEX IF NOT EXISTS idx_payout_items_batch_status
    ON seymour_engine.payout_items (payout_batch_id, status);

CREATE TABLE IF NOT EXISTS seymour_engine.payout_events (
    payout_event_id UUID PRIMARY KEY,
    payout_batch_id UUID NOT NULL REFERENCES seymour_engine.payout_batches(payout_batch_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payout_events_batch_time
    ON seymour_engine.payout_events (payout_batch_id, created_at);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('013_payout_engine')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
