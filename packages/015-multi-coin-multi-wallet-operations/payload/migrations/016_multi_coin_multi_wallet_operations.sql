BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.coin_registry (
    coin_code TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    family TEXT NOT NULL DEFAULT 'utxo',
    decimals SMALLINT NOT NULL DEFAULT 8 CHECK (decimals BETWEEN 0 AND 18),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.coin_networks (
    coin_code TEXT NOT NULL REFERENCES seymour_engine.coin_registry(coin_code) ON DELETE RESTRICT,
    network TEXT NOT NULL CHECK (network IN ('mainnet','testnet','regtest')),
    rpc_chain_name TEXT,
    confirmations_required INTEGER NOT NULL DEFAULT 1 CHECK (confirmations_required >= 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (coin_code, network)
);

ALTER TABLE seymour_engine.wallets
    ADD COLUMN IF NOT EXISTS wallet_role TEXT NOT NULL DEFAULT 'primary-hot',
    ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100,
    ADD COLUMN IF NOT EXISTS label TEXT,
    ADD COLUMN IF NOT EXISTS spend_enabled BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE seymour_engine.wallets DROP CONSTRAINT IF EXISTS ck_wallet_role;
ALTER TABLE seymour_engine.wallets ADD CONSTRAINT ck_wallet_role CHECK (
    wallet_role IN ('primary-hot','secondary-hot','reserve','cold-storage','pool-payout',
                    'developer','pool-fee','treasury','exchange','backup')
);
CREATE INDEX IF NOT EXISTS idx_wallets_selection
    ON seymour_engine.wallets (coin, network, wallet_role, status, priority);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_assignments (
    wallet_assignment_id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    assignment_scope TEXT NOT NULL CHECK (assignment_scope IN ('global','pool','developer-fee','pool-fee','treasury','exchange')),
    scope_key TEXT NOT NULL DEFAULT '*',
    purpose TEXT NOT NULL CHECK (purpose IN ('payout','fee-receipt','reserve','treasury','exchange','backup')),
    priority INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_by TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_wallet_assignment UNIQUE (wallet_id, assignment_scope, scope_key, purpose)
);
CREATE INDEX IF NOT EXISTS idx_wallet_assignments_lookup
    ON seymour_engine.wallet_assignments (assignment_scope, scope_key, purpose, enabled, priority);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_selection_policies (
    wallet_selection_policy_id UUID PRIMARY KEY,
    coin TEXT NOT NULL,
    network TEXT NOT NULL CHECK (network IN ('mainnet','testnet','regtest')),
    assignment_scope TEXT NOT NULL CHECK (assignment_scope IN ('global','pool','developer-fee','pool-fee','treasury','exchange')),
    scope_key TEXT NOT NULL DEFAULT '*',
    purpose TEXT NOT NULL CHECK (purpose IN ('payout','fee-receipt','reserve','treasury','exchange','backup')),
    strategy TEXT NOT NULL DEFAULT 'priority' CHECK (strategy IN ('priority','highest-available','round-robin','manual')),
    allow_failover BOOLEAN NOT NULL DEFAULT TRUE,
    minimum_health_status TEXT NOT NULL DEFAULT 'healthy' CHECK (minimum_health_status IN ('healthy','degraded')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_wallet_selection_policy UNIQUE (coin, network, assignment_scope, scope_key, purpose)
);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_reserves (
    wallet_id UUID PRIMARY KEY REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    minimum_balance NUMERIC(30,12) NOT NULL DEFAULT 0 CHECK (minimum_balance >= 0),
    target_balance NUMERIC(30,12) CHECK (target_balance IS NULL OR target_balance >= minimum_balance),
    maximum_single_payout NUMERIC(30,12) CHECK (maximum_single_payout IS NULL OR maximum_single_payout > 0),
    action_below_minimum TEXT NOT NULL DEFAULT 'block' CHECK (action_below_minimum IN ('block','warn','failover')),
    updated_by TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_balance_snapshots (
    wallet_balance_snapshot_id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    confirmed_balance NUMERIC(30,12) NOT NULL DEFAULT 0,
    unconfirmed_balance NUMERIC(30,12) NOT NULL DEFAULT 0,
    locked_balance NUMERIC(30,12) NOT NULL DEFAULT 0,
    available_balance NUMERIC(30,12) NOT NULL DEFAULT 0,
    block_height BIGINT,
    observed_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wallet_balance_latest
    ON seymour_engine.wallet_balance_snapshots (wallet_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_health (
    wallet_id UUID PRIMARY KEY REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    health_status TEXT NOT NULL CHECK (health_status IN ('healthy','degraded','unhealthy','unknown')),
    rpc_reachable BOOLEAN NOT NULL DEFAULT FALSE,
    node_synced BOOLEAN NOT NULL DEFAULT FALSE,
    wallet_unlocked BOOLEAN,
    spendable BOOLEAN NOT NULL DEFAULT FALSE,
    address_valid BOOLEAN,
    checked_at TIMESTAMPTZ NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_reconciliation_events (
    wallet_reconciliation_event_id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    ledger_balance NUMERIC(30,12) NOT NULL,
    blockchain_balance NUMERIC(30,12) NOT NULL,
    difference NUMERIC(30,12) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('matched','drift','error')),
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wallet_reconciliation_latest
    ON seymour_engine.wallet_reconciliation_events (wallet_id, created_at DESC);

INSERT INTO seymour_engine.coin_registry (coin_code, display_name)
VALUES ('BTC','Bitcoin'), ('BCH','Bitcoin Cash'), ('LTC','Litecoin'), ('DOGE','Dogecoin')
ON CONFLICT (coin_code) DO NOTHING;

INSERT INTO seymour_engine.coin_networks (coin_code, network, confirmations_required)
SELECT coin_code, network, CASE WHEN network='mainnet' THEN 1 ELSE 0 END
FROM seymour_engine.coin_registry CROSS JOIN (VALUES ('mainnet'),('testnet'),('regtest')) AS n(network)
ON CONFLICT (coin_code, network) DO NOTHING;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('016_multi_coin_multi_wallet_operations')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
