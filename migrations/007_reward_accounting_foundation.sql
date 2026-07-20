BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.reward_periods (
    reward_period_id UUID PRIMARY KEY,
    block_id UUID NOT NULL REFERENCES seymour_engine.blocks(block_id) ON DELETE RESTRICT,
    pool_id TEXT NOT NULL,
    calculation_method TEXT NOT NULL DEFAULT 'proportional',
    status TEXT NOT NULL DEFAULT 'immature',
    gross_reward NUMERIC(28, 12) NOT NULL,
    pool_fee NUMERIC(28, 12) NOT NULL DEFAULT 0,
    distributable_reward NUMERIC(28, 12) NOT NULL,
    total_accepted_difficulty NUMERIC(36, 12) NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_reward_period_block UNIQUE (block_id),
    CONSTRAINT ck_reward_period_method CHECK (calculation_method IN ('proportional')),
    CONSTRAINT ck_reward_period_status CHECK (status IN ('immature', 'confirmed', 'reversed')),
    CONSTRAINT ck_reward_period_amounts CHECK (
        gross_reward >= 0 AND pool_fee >= 0 AND distributable_reward >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_reward_periods_pool_status
    ON seymour_engine.reward_periods (pool_id, status, calculated_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.worker_reward_entries (
    reward_entry_id UUID PRIMARY KEY,
    reward_period_id UUID NOT NULL REFERENCES seymour_engine.reward_periods(reward_period_id) ON DELETE CASCADE,
    worker_id UUID REFERENCES seymour_engine.workers(worker_id) ON DELETE SET NULL,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    accepted_difficulty NUMERIC(36, 12) NOT NULL DEFAULT 0,
    reward_amount NUMERIC(28, 12) NOT NULL,
    status TEXT NOT NULL DEFAULT 'immature',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_worker_reward_period_identity UNIQUE (
        reward_period_id, pool_id, miner, worker
    ),
    CONSTRAINT ck_worker_reward_status CHECK (status IN ('immature', 'confirmed', 'reversed')),
    CONSTRAINT ck_worker_reward_amount CHECK (reward_amount >= 0),
    CONSTRAINT ck_worker_reward_difficulty CHECK (accepted_difficulty >= 0)
);

CREATE INDEX IF NOT EXISTS idx_worker_rewards_identity_status
    ON seymour_engine.worker_reward_entries (pool_id, miner, worker, status);

CREATE TABLE IF NOT EXISTS seymour_engine.balance_ledger (
    ledger_entry_id UUID PRIMARY KEY,
    reward_entry_id UUID REFERENCES seymour_engine.worker_reward_entries(reward_entry_id) ON DELETE RESTRICT,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    entry_type TEXT NOT NULL,
    amount NUMERIC(28, 12) NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reference_type TEXT NOT NULL,
    reference_id UUID,
    idempotency_key TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_balance_ledger_idempotency UNIQUE (idempotency_key),
    CONSTRAINT ck_balance_ledger_type CHECK (
        entry_type IN ('immature_credit', 'immature_debit', 'confirmed_credit',
                       'confirmed_debit', 'payout_debit', 'adjustment')
    ),
    CONSTRAINT ck_balance_ledger_amount CHECK (amount <> 0)
);

CREATE INDEX IF NOT EXISTS idx_balance_ledger_identity_time
    ON seymour_engine.balance_ledger (pool_id, miner, worker, effective_at DESC);

CREATE OR REPLACE VIEW seymour_engine.worker_balances AS
SELECT
    pool_id,
    miner,
    worker,
    COALESCE(SUM(CASE
        WHEN entry_type IN ('immature_credit') THEN amount
        WHEN entry_type IN ('immature_debit') THEN amount
        ELSE 0 END), 0)::NUMERIC(28, 12) AS immature_balance,
    COALESCE(SUM(CASE
        WHEN entry_type IN ('confirmed_credit', 'adjustment') THEN amount
        WHEN entry_type IN ('confirmed_debit', 'payout_debit') THEN amount
        ELSE 0 END), 0)::NUMERIC(28, 12) AS confirmed_balance,
    MAX(effective_at) AS updated_at
FROM seymour_engine.balance_ledger
GROUP BY pool_id, miner, worker;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('007_reward_accounting_foundation')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
