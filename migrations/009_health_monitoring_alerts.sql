BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.health_observations (
    health_observation_id UUID PRIMARY KEY,
    scope_type TEXT NOT NULL,
    scope_id TEXT,
    component TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'warning', 'critical', 'disabled')),
    summary TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_health_observations_scope_time
    ON seymour_engine.health_observations
    (scope_type, scope_id, component, observed_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.alert_rules (
    alert_rule_id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    component TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    warning_after INTEGER NOT NULL DEFAULT 1 CHECK (warning_after > 0),
    critical_after INTEGER NOT NULL DEFAULT 1 CHECK (critical_after > 0),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.alerts (
    alert_id UUID PRIMARY KEY,
    alert_rule_id UUID REFERENCES seymour_engine.alert_rules(alert_rule_id)
        ON DELETE SET NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT,
    component TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('warning', 'critical')),
    status TEXT NOT NULL CHECK (status IN ('open', 'acknowledged', 'resolved', 'suppressed')),
    fingerprint TEXT NOT NULL,
    summary TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurrence_count INTEGER NOT NULL DEFAULT 1 CHECK (occurrence_count > 0),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    resolved_at TIMESTAMPTZ,
    suppressed_until TIMESTAMPTZ,
    suppression_reason TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_alerts_active_fingerprint
    ON seymour_engine.alerts (fingerprint)
    WHERE status IN ('open', 'acknowledged', 'suppressed');

CREATE INDEX IF NOT EXISTS ix_alerts_status_severity_time
    ON seymour_engine.alerts (status, severity, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.alert_events (
    alert_event_id UUID PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES seymour_engine.alerts(alert_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('opened', 'updated', 'acknowledged', 'resolved', 'suppressed', 'reopened')
    ),
    actor TEXT,
    message TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alert_events_alert_time
    ON seymour_engine.alert_events (alert_id, occurred_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('009_health_monitoring_alerts')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
