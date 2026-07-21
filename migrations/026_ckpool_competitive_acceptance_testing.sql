BEGIN;
CREATE TABLE IF NOT EXISTS seymour_engine.acceptance_test_runs (
    run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    profile text NOT NULL,
    status text NOT NULL CHECK (status IN ('running','passed','failed')),
    checks_total integer NOT NULL DEFAULT 0,
    checks_passed integer NOT NULL DEFAULT 0,
    duration_ms numeric(14,3),
    report jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE INDEX IF NOT EXISTS idx_acceptance_test_runs_started ON seymour_engine.acceptance_test_runs(started_at DESC);
INSERT INTO seymour_engine.schema_migrations(migration_id)
VALUES ('026_ckpool_competitive_acceptance_testing') ON CONFLICT DO NOTHING;
COMMIT;
