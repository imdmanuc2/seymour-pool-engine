BEGIN;

CREATE INDEX IF NOT EXISTS ix_stratum_submissions_created_worker
    ON seymour_engine.stratum_submissions(created_at DESC, worker_name)
    INCLUDE (session_id, accepted, reject_reason);

CREATE INDEX IF NOT EXISTS ix_stratum_submissions_worker_created
    ON seymour_engine.stratum_submissions(worker_name, created_at DESC)
    INCLUDE (session_id, accepted, reject_reason);

CREATE INDEX IF NOT EXISTS ix_stratum_difficulty_history_session_created
    ON seymour_engine.stratum_difficulty_history(session_id, created_at DESC)
    INCLUDE (new_difficulty);

CREATE INDEX IF NOT EXISTS ix_stratum_sessions_worker_active
    ON seymour_engine.stratum_sessions(worker_name, disconnected_at, connected_at DESC)
    INCLUDE (authorized, difficulty, last_activity_at, last_share_at);

CREATE TABLE IF NOT EXISTS seymour_engine.native_statistics_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('engine', 'pool', 'worker')),
    scope_id TEXT NOT NULL,
    window_seconds INTEGER NOT NULL CHECK (window_seconds > 0),
    hashrate_hs NUMERIC(38, 4) NOT NULL DEFAULT 0,
    accepted_shares BIGINT NOT NULL DEFAULT 0,
    rejected_shares BIGINT NOT NULL DEFAULT 0,
    active_workers INTEGER NOT NULL DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_native_statistics_scope_time
    ON seymour_engine.native_statistics_snapshots(
        scope_type, scope_id, window_seconds, calculated_at DESC
    );

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('026_native_hashrate_pool_statistics')
ON CONFLICT DO NOTHING;

COMMIT;
