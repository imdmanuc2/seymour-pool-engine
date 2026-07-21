BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.backup_profiles (
    backup_profile_id UUID PRIMARY KEY,
    profile_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    backup_type TEXT NOT NULL CHECK (backup_type IN ('database','configuration','wallet_metadata','full')),
    schedule_expression TEXT,
    retention_days INTEGER NOT NULL DEFAULT 30 CHECK (retention_days >= 1),
    encryption_required BOOLEAN NOT NULL DEFAULT TRUE,
    compression TEXT NOT NULL DEFAULT 'gzip' CHECK (compression IN ('none','gzip','zstd')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.backup_targets (
    backup_target_id UUID PRIMARY KEY,
    target_key TEXT NOT NULL UNIQUE,
    target_type TEXT NOT NULL CHECK (target_type IN ('filesystem','object_storage','remote_host')),
    location TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    encryption_key_reference TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.backup_runs (
    backup_run_id UUID PRIMARY KEY,
    backup_profile_id UUID NOT NULL REFERENCES seymour_engine.backup_profiles(backup_profile_id),
    backup_target_id UUID NOT NULL REFERENCES seymour_engine.backup_targets(backup_target_id),
    status TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
    requested_by TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    recovery_point_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_backup_runs_status_created ON seymour_engine.backup_runs(status, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.backup_artifacts (
    backup_artifact_id UUID PRIMARY KEY,
    backup_run_id UUID NOT NULL REFERENCES seymour_engine.backup_runs(backup_run_id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    sha256_checksum TEXT NOT NULL,
    encrypted BOOLEAN NOT NULL DEFAULT FALSE,
    encryption_algorithm TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (backup_run_id, relative_path)
);

CREATE TABLE IF NOT EXISTS seymour_engine.backup_integrity_checks (
    backup_integrity_check_id UUID PRIMARY KEY,
    backup_artifact_id UUID NOT NULL REFERENCES seymour_engine.backup_artifacts(backup_artifact_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('passed','failed')),
    expected_checksum TEXT NOT NULL,
    observed_checksum TEXT,
    checked_by TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS seymour_engine.restore_runs (
    restore_run_id UUID PRIMARY KEY,
    backup_run_id UUID NOT NULL REFERENCES seymour_engine.backup_runs(backup_run_id),
    mode TEXT NOT NULL CHECK (mode IN ('validate','restore')),
    status TEXT NOT NULL CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
    requested_by TEXT NOT NULL,
    target_environment TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.health_snapshots (
    health_snapshot_id UUID PRIMARY KEY,
    snapshot_type TEXT NOT NULL,
    overall_status TEXT NOT NULL,
    components JSONB NOT NULL DEFAULT '{}'::jsonb,
    captured_by TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.disaster_recovery_playbooks (
    disaster_recovery_playbook_id UUID PRIMARY KEY,
    playbook_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_validated_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.backup_events (
    backup_event_id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'info',
    backup_run_id UUID REFERENCES seymour_engine.backup_runs(backup_run_id),
    restore_run_id UUID REFERENCES seymour_engine.restore_runs(restore_run_id),
    message TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_backup_events_created ON seymour_engine.backup_events(created_at DESC);

INSERT INTO seymour_engine.backup_profiles (
    backup_profile_id, profile_key, display_name, backup_type, schedule_expression,
    retention_days, encryption_required, compression
) VALUES
(gen_random_uuid(), 'daily-database', 'Daily PostgreSQL Backup', 'database', '0 2 * * *', 30, TRUE, 'gzip'),
(gen_random_uuid(), 'daily-configuration', 'Daily Configuration Backup', 'configuration', '15 2 * * *', 30, TRUE, 'gzip'),
(gen_random_uuid(), 'daily-wallet-metadata', 'Daily Wallet Metadata Backup', 'wallet_metadata', '30 2 * * *', 30, TRUE, 'gzip')
ON CONFLICT (profile_key) DO NOTHING;

INSERT INTO seymour_engine.disaster_recovery_playbooks (
    disaster_recovery_playbook_id, playbook_key, display_name, steps
) VALUES (
    gen_random_uuid(), 'engine-host-recovery', 'Pool Engine Host Recovery',
    '[{"order":1,"action":"isolate_failed_host"},{"order":2,"action":"verify_latest_backup"},{"order":3,"action":"restore_database"},{"order":4,"action":"restore_configuration"},{"order":5,"action":"validate_wallet_metadata"},{"order":6,"action":"run_health_checks"},{"order":7,"action":"resume_services"}]'::jsonb
) ON CONFLICT (playbook_key) DO NOTHING;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('018_reliability_backup_disaster_recovery')
ON CONFLICT (migration_id) DO NOTHING;
COMMIT;
