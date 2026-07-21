BEGIN;

ALTER TABLE seymour_engine.stratum_sessions
    ADD COLUMN IF NOT EXISTS accepted_shares BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_share_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS share_interval_ewma DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS vardiff_last_retarget_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS vardiff_share_baseline BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS difficulty_changes INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS seymour_engine.stratum_difficulty_history (
    difficulty_event_id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES seymour_engine.stratum_sessions(session_id) ON DELETE SET NULL,
    worker_name TEXT,
    old_difficulty NUMERIC(30, 12) NOT NULL,
    new_difficulty NUMERIC(30, 12) NOT NULL,
    observed_share_seconds DOUBLE PRECISION,
    target_share_seconds DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stratum_difficulty_history_session
    ON seymour_engine.stratum_difficulty_history(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_stratum_sessions_vardiff_active
    ON seymour_engine.stratum_sessions(disconnected_at, last_share_at DESC)
    WHERE disconnected_at IS NULL;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('024_variable_difficulty_scaling')
ON CONFLICT DO NOTHING;

COMMIT;
