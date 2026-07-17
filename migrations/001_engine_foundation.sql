BEGIN;

CREATE SCHEMA IF NOT EXISTS seymour_engine;

CREATE TABLE IF NOT EXISTS seymour_engine.schema_migrations (
    migration_id TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.installations (
    installation_id UUID PRIMARY KEY,
    display_name TEXT NOT NULL,
    environment TEXT NOT NULL DEFAULT 'production',
    hostname TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('001_engine_foundation')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
