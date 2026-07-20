BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.fee_profiles (
    fee_profile_id UUID PRIMARY KEY,
    pool_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    developer_fee_percent NUMERIC(7,4) NOT NULL DEFAULT 0.7500,
    operator_fee_percent NUMERIC(7,4) NOT NULL DEFAULT 0,
    developer_destination TEXT NOT NULL,
    operator_destination TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_fee_profile_pool_coin UNIQUE (pool_id, coin),
    CONSTRAINT ck_developer_fee_minimum CHECK (developer_fee_percent >= 0.7500),
    CONSTRAINT ck_developer_fee_maximum CHECK (developer_fee_percent <= 100),
    CONSTRAINT ck_operator_fee_range CHECK (operator_fee_percent >= 0 AND operator_fee_percent <= 100),
    CONSTRAINT ck_total_fee_range CHECK (developer_fee_percent + operator_fee_percent < 100)
);

CREATE TABLE IF NOT EXISTS seymour_engine.reward_calculations (
    reward_calculation_id UUID PRIMARY KEY,
    block_id UUID NOT NULL REFERENCES seymour_engine.blocks(block_id) ON DELETE RESTRICT,
    fee_profile_id UUID NOT NULL REFERENCES seymour_engine.fee_profiles(fee_profile_id) ON DELETE RESTRICT,
    pool_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    policy TEXT NOT NULL,
    gross_reward NUMERIC(28,12) NOT NULL,
    developer_fee_percent NUMERIC(7,4) NOT NULL,
    developer_fee_amount NUMERIC(28,12) NOT NULL,
    operator_fee_percent NUMERIC(7,4) NOT NULL,
    operator_fee_amount NUMERIC(28,12) NOT NULL,
    worker_reward_amount NUMERIC(28,12) NOT NULL,
    integrity_hash TEXT NOT NULL,
    previous_integrity_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_reward_calculation_block UNIQUE (block_id),
    CONSTRAINT ck_reward_policy CHECK (policy IN ('solo', 'prop', 'pplns')),
    CONSTRAINT ck_calculation_dev_minimum CHECK (developer_fee_percent >= 0.7500),
    CONSTRAINT ck_reward_calculation_amounts CHECK (
        gross_reward > 0 AND developer_fee_amount >= 0 AND
        operator_fee_amount >= 0 AND worker_reward_amount >= 0 AND
        developer_fee_amount + operator_fee_amount + worker_reward_amount = gross_reward
    )
);

CREATE INDEX IF NOT EXISTS idx_reward_calculations_pool_created
    ON seymour_engine.reward_calculations (pool_id, coin, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.reward_allocations (
    reward_allocation_id UUID PRIMARY KEY,
    reward_calculation_id UUID NOT NULL REFERENCES seymour_engine.reward_calculations(reward_calculation_id) ON DELETE RESTRICT,
    allocation_type TEXT NOT NULL,
    recipient_key TEXT NOT NULL,
    amount NUMERIC(28,12) NOT NULL,
    weight NUMERIC(36,12),
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_reward_allocation_idempotency UNIQUE (idempotency_key),
    CONSTRAINT ck_reward_allocation_type CHECK (allocation_type IN ('developer', 'operator', 'worker')),
    CONSTRAINT ck_reward_allocation_amount CHECK (amount >= 0)
);

CREATE INDEX IF NOT EXISTS idx_reward_allocations_calculation
    ON seymour_engine.reward_allocations (reward_calculation_id, allocation_type);

CREATE TABLE IF NOT EXISTS seymour_engine.reward_calculation_events (
    reward_calculation_event_id UUID PRIMARY KEY,
    reward_calculation_id UUID NOT NULL REFERENCES seymour_engine.reward_calculations(reward_calculation_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL,
    event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    integrity_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('010_developer_fee_pool_economics')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
