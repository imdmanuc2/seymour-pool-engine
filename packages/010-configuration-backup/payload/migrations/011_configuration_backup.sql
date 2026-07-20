BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.configuration_profiles (
    configuration_profile_id UUID PRIMARY KEY,
    profile_key TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    active_revision_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT ck_configuration_domain CHECK (
        domain IN ('engine','pool','coin','rpc','stratum','wallet-reference',
                   'reward-policy','developer-fee','logging','monitoring','api','security')
    )
);

CREATE TABLE IF NOT EXISTS seymour_engine.configuration_revisions (
    configuration_revision_id UUID PRIMARY KEY,
    configuration_profile_id UUID NOT NULL
        REFERENCES seymour_engine.configuration_profiles(configuration_profile_id) ON DELETE RESTRICT,
    revision_number INTEGER NOT NULL,
    configuration JSONB NOT NULL,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    change_summary TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    previous_revision_id UUID
        REFERENCES seymour_engine.configuration_revisions(configuration_revision_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_configuration_revision UNIQUE (configuration_profile_id, revision_number),
    CONSTRAINT ck_configuration_revision_status CHECK (status IN ('active','superseded','rolled-back'))
);

ALTER TABLE seymour_engine.configuration_profiles
    DROP CONSTRAINT IF EXISTS fk_configuration_profiles_active_revision;
ALTER TABLE seymour_engine.configuration_profiles
    ADD CONSTRAINT fk_configuration_profiles_active_revision
    FOREIGN KEY (active_revision_id)
    REFERENCES seymour_engine.configuration_revisions(configuration_revision_id)
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_configuration_revisions_profile_created
    ON seymour_engine.configuration_revisions (configuration_profile_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.configuration_validation_results (
    configuration_validation_result_id UUID PRIMARY KEY,
    profile_key TEXT NOT NULL,
    domain TEXT NOT NULL,
    valid BOOLEAN NOT NULL,
    errors JSONB NOT NULL DEFAULT '[]'::JSONB,
    warnings JSONB NOT NULL DEFAULT '[]'::JSONB,
    configuration_checksum TEXT NOT NULL,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS seymour_engine.configuration_exports (
    configuration_export_id UUID PRIMARY KEY,
    export_version INTEGER NOT NULL DEFAULT 1,
    profile_count INTEGER NOT NULL,
    payload_checksum TEXT NOT NULL,
    exported_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS seymour_engine.configuration_imports (
    configuration_import_id UUID PRIMARY KEY,
    export_version INTEGER NOT NULL,
    payload_checksum TEXT NOT NULL,
    imported_by TEXT NOT NULL,
    status TEXT NOT NULL,
    profile_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT ck_configuration_import_status CHECK (status IN ('completed','rejected','failed'))
);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('011_configuration_backup')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
