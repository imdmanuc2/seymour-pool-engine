BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.bitcoin_block_templates (
    template_id BIGSERIAL PRIMARY KEY,
    height BIGINT NOT NULL,
    previous_block_hash TEXT NOT NULL,
    version INTEGER NOT NULL,
    bits TEXT NOT NULL,
    target TEXT,
    curtime BIGINT NOT NULL,
    mintime BIGINT NOT NULL,
    coinbase_value BIGINT NOT NULL,
    transaction_count INTEGER NOT NULL,
    work_id TEXT,
    longpoll_id TEXT,
    raw_template JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_bitcoin_block_templates_active
    ON seymour_engine.bitcoin_block_templates(active, height DESC, received_at DESC);

ALTER TABLE seymour_engine.stratum_jobs
    ADD COLUMN IF NOT EXISTS template_height BIGINT,
    ADD COLUMN IF NOT EXISTS coinbase_value BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS transaction_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS work_id TEXT;

CREATE INDEX IF NOT EXISTS ix_stratum_jobs_active_created
    ON seymour_engine.stratum_jobs(active, created_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('021_bitcoin_template_job_engine')
ON CONFLICT DO NOTHING;

COMMIT;
