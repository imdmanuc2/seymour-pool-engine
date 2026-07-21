BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.stratum_sessions (
    session_id UUID PRIMARY KEY,
    remote_host TEXT NOT NULL,
    remote_port INTEGER,
    user_agent TEXT,
    worker_name TEXT,
    subscribed BOOLEAN NOT NULL DEFAULT FALSE,
    authorized BOOLEAN NOT NULL DEFAULT FALSE,
    difficulty NUMERIC(30, 12) NOT NULL DEFAULT 1,
    extranonce1 TEXT NOT NULL,
    extranonce2_size INTEGER NOT NULL DEFAULT 4,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMPTZ,
    disconnect_reason TEXT,
    messages_received BIGINT NOT NULL DEFAULT 0,
    messages_sent BIGINT NOT NULL DEFAULT 0,
    submissions_received BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_stratum_sessions_active
    ON seymour_engine.stratum_sessions(disconnected_at, connected_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.stratum_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES seymour_engine.stratum_sessions(session_id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    method TEXT,
    request_id TEXT,
    success BOOLEAN,
    error_code INTEGER,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stratum_messages_session
    ON seymour_engine.stratum_messages(session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.stratum_jobs (
    job_id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'synthetic',
    previous_block_hash TEXT NOT NULL,
    coinbase1 TEXT NOT NULL,
    coinbase2 TEXT NOT NULL,
    merkle_branches JSONB NOT NULL DEFAULT '[]'::jsonb,
    version TEXT NOT NULL,
    nbits TEXT NOT NULL,
    ntime TEXT NOT NULL,
    clean_jobs BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.stratum_submissions (
    submission_id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES seymour_engine.stratum_sessions(session_id) ON DELETE SET NULL,
    job_id TEXT,
    worker_name TEXT,
    extranonce2 TEXT,
    ntime TEXT,
    nonce TEXT,
    accepted BOOLEAN NOT NULL,
    reject_reason TEXT,
    validation_mode TEXT NOT NULL DEFAULT 'protocol-placeholder',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_stratum_submissions_session
    ON seymour_engine.stratum_submissions(session_id, created_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('020_stratum_protocol_foundation')
ON CONFLICT DO NOTHING;

COMMIT;
