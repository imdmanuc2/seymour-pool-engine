BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.diagnostic_runs (
    diagnostic_run_id UUID PRIMARY KEY,
    pool_id TEXT,
    operation TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'passed', 'degraded', 'failed')),
    readiness_score INTEGER NOT NULL DEFAULT 0 CHECK (readiness_score BETWEEN 0 AND 100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    summary TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS ix_diagnostic_runs_pool_started
    ON seymour_engine.diagnostic_runs (pool_id, started_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.diagnostic_checks (
    diagnostic_check_id UUID PRIMARY KEY,
    diagnostic_run_id UUID NOT NULL REFERENCES seymour_engine.diagnostic_runs(diagnostic_run_id)
        ON DELETE CASCADE,
    component TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('passed', 'warning', 'failed', 'disabled')),
    summary TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_diagnostic_checks_run
    ON seymour_engine.diagnostic_checks (diagnostic_run_id, component);

INSERT INTO seymour_engine.schema_migrations (migration_id, description)
VALUES ('008_pool_operations_diagnostics', 'Pool operations and diagnostics')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
