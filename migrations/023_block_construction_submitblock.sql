BEGIN;
CREATE TABLE IF NOT EXISTS seymour_engine.bitcoin_block_candidates (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id BIGINT,
    job_id TEXT NOT NULL,
    template_height BIGINT NOT NULL,
    block_hash TEXT NOT NULL,
    header_hex TEXT NOT NULL,
    block_hex TEXT NOT NULL,
    transaction_count INTEGER NOT NULL,
    work_id TEXT,
    submit_status TEXT NOT NULL DEFAULT 'pending',
    submit_result TEXT,
    submit_error TEXT,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ux_bitcoin_block_candidates_hash UNIQUE(block_hash)
);
CREATE INDEX IF NOT EXISTS ix_bitcoin_block_candidates_status
    ON seymour_engine.bitcoin_block_candidates(submit_status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_bitcoin_block_candidates_height
    ON seymour_engine.bitcoin_block_candidates(template_height DESC);
INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('023_block_construction_submitblock') ON CONFLICT DO NOTHING;
COMMIT;
