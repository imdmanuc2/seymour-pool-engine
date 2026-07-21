BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.coinbase_maturity_policies (
    policy_id UUID PRIMARY KEY,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    required_confirmations INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_coinbase_maturity_policy UNIQUE (coin, network),
    CONSTRAINT ck_coinbase_required_confirmations CHECK (required_confirmations > 0)
);

CREATE TABLE IF NOT EXISTS seymour_engine.coinbase_maturity_records (
    maturity_record_id UUID PRIMARY KEY,
    block_id UUID NOT NULL REFERENCES seymour_engine.blocks(block_id) ON DELETE RESTRICT,
    pool_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    block_height BIGINT NOT NULL,
    block_hash TEXT,
    confirmations INTEGER NOT NULL DEFAULT 0,
    required_confirmations INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'immature',
    observed_tip_height BIGINT,
    first_observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    matured_at TIMESTAMPTZ,
    orphaned_at TIMESTAMPTZ,
    reconciled_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_coinbase_maturity_block UNIQUE (block_id),
    CONSTRAINT ck_coinbase_maturity_status CHECK (
        status IN ('immature', 'mature', 'orphaned')
    ),
    CONSTRAINT ck_coinbase_maturity_confirmations CHECK (
        confirmations >= 0 AND required_confirmations > 0
    )
);

CREATE INDEX IF NOT EXISTS idx_coinbase_maturity_pool_status
    ON seymour_engine.coinbase_maturity_records (pool_id, status, last_observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_coinbase_maturity_coin_network
    ON seymour_engine.coinbase_maturity_records (coin, network, status);

CREATE TABLE IF NOT EXISTS seymour_engine.coinbase_maturity_events (
    maturity_event_id UUID PRIMARY KEY,
    maturity_record_id UUID NOT NULL
        REFERENCES seymour_engine.coinbase_maturity_records(maturity_record_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    confirmations INTEGER NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_coinbase_maturity_event_type CHECK (
        event_type IN ('observed', 'confirmation_updated', 'matured', 'orphaned', 'reconciled')
    )
);

CREATE INDEX IF NOT EXISTS idx_coinbase_maturity_events_record_time
    ON seymour_engine.coinbase_maturity_events (maturity_record_id, created_at DESC);

INSERT INTO seymour_engine.coinbase_maturity_policies (
    policy_id, coin, network, required_confirmations, created_by
) VALUES
    (gen_random_uuid(), 'BTC', 'mainnet', 100, 'migration-014'),
    (gen_random_uuid(), 'BCH', 'mainnet', 100, 'migration-014')
ON CONFLICT (coin, network) DO NOTHING;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('014_coinbase_maturity_tracking')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
