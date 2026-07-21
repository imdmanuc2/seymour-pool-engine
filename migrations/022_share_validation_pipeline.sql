BEGIN;
ALTER TABLE seymour_engine.stratum_submissions
    ADD COLUMN IF NOT EXISTS submission_fingerprint TEXT,
    ADD COLUMN IF NOT EXISTS share_hash TEXT,
    ADD COLUMN IF NOT EXISTS share_difficulty NUMERIC(38, 16),
    ADD COLUMN IF NOT EXISTS block_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS header_hex TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS ux_stratum_submissions_fingerprint
    ON seymour_engine.stratum_submissions(submission_fingerprint)
    WHERE submission_fingerprint IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_stratum_submissions_validation
    ON seymour_engine.stratum_submissions(accepted, block_candidate, created_at DESC);
INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('022_share_validation_pipeline') ON CONFLICT DO NOTHING;
COMMIT;
