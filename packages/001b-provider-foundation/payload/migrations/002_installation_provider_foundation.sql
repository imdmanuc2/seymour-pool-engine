BEGIN;

ALTER TABLE seymour_engine.installations
    ADD COLUMN IF NOT EXISTS engine_version TEXT,
    ADD COLUMN IF NOT EXISTS provider_name TEXT,
    ADD COLUMN IF NOT EXISTS provider_version TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_installations_last_seen
    ON seymour_engine.installations (last_seen_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('002_installation_provider_foundation')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
