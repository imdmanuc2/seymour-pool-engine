BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.wallets (
    wallet_id UUID PRIMARY KEY,
    wallet_key TEXT NOT NULL UNIQUE,
    pool_id TEXT,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    purpose TEXT NOT NULL,
    address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    validation_status TEXT NOT NULL DEFAULT 'pending',
    validated_at TIMESTAMPTZ,
    descriptor_reference TEXT,
    secret_reference TEXT,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_wallet_coin_network_address UNIQUE (coin, network, address),
    CONSTRAINT ck_wallet_network CHECK (network IN ('mainnet','testnet','regtest')),
    CONSTRAINT ck_wallet_purpose CHECK (purpose IN ('developer','operator','pool','payout','reserve','cold-storage')),
    CONSTRAINT ck_wallet_status CHECK (status IN ('active','standby','retired')),
    CONSTRAINT ck_wallet_validation CHECK (validation_status IN ('pending','valid','invalid')),
    CONSTRAINT ck_wallet_secret_reference CHECK (secret_reference IS NULL OR length(secret_reference) > 0)
);

CREATE INDEX IF NOT EXISTS idx_wallets_pool_coin_status
    ON seymour_engine.wallets (pool_id, coin, status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_developer_wallet_per_coin_network
    ON seymour_engine.wallets (coin, network)
    WHERE purpose='developer' AND status='active';

CREATE TABLE IF NOT EXISTS seymour_engine.wallet_events (
    wallet_event_id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_wallet_event_type CHECK (
        event_type IN ('created','updated','validated','activated','standby','retired')
    )
);

CREATE INDEX IF NOT EXISTS idx_wallet_events_wallet_created
    ON seymour_engine.wallet_events (wallet_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.worker_payout_addresses (
    worker_payout_address_id UUID PRIMARY KEY,
    worker_id UUID NOT NULL REFERENCES seymour_engine.workers(worker_id) ON DELETE RESTRICT,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    validation_status TEXT NOT NULL DEFAULT 'pending',
    validated_at TIMESTAMPTZ,
    changed_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_worker_payout_coin_network UNIQUE (worker_id, coin, network),
    CONSTRAINT ck_worker_payout_network CHECK (network IN ('mainnet','testnet','regtest')),
    CONSTRAINT ck_worker_payout_status CHECK (status IN ('active','retired')),
    CONSTRAINT ck_worker_payout_validation CHECK (validation_status IN ('pending','valid','invalid'))
);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('012_wallet_management')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
