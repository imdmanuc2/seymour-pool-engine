BEGIN;

ALTER TABLE seymour_engine.shares
    ADD COLUMN IF NOT EXISTS share_status TEXT NOT NULL DEFAULT 'accepted';

ALTER TABLE seymour_engine.shares
    DROP CONSTRAINT IF EXISTS ck_shares_status;

ALTER TABLE seymour_engine.shares
    ADD CONSTRAINT ck_shares_status
    CHECK (share_status IN ('accepted', 'rejected', 'stale'));

CREATE INDEX IF NOT EXISTS idx_shares_statistics_window
    ON seymour_engine.shares (provider_created_at DESC, pool_id, worker_id, share_status);

CREATE TABLE IF NOT EXISTS seymour_engine.statistics_snapshots (
    snapshot_id UUID PRIMARY KEY,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('platform', 'pool', 'worker')),
    scope_id TEXT NOT NULL,
    window_seconds INTEGER NOT NULL CHECK (window_seconds > 0),
    hashrate DOUBLE PRECISION NOT NULL DEFAULT 0,
    accepted_shares BIGINT NOT NULL DEFAULT 0,
    rejected_shares BIGINT NOT NULL DEFAULT 0,
    stale_shares BIGINT NOT NULL DEFAULT 0,
    efficiency DOUBLE PRECISION NOT NULL DEFAULT 0,
    active_workers INTEGER NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_statistics_snapshots_scope_time
    ON seymour_engine.statistics_snapshots
    (scope_type, scope_id, window_seconds, calculated_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('005_statistics_engine')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
