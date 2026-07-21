BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.bitcoin_rpc_failover_events (
    event_id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_bitcoin_rpc_failover_events_created_at
    ON seymour_engine.bitcoin_rpc_failover_events (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_bitcoin_rpc_failover_events_endpoint
    ON seymour_engine.bitcoin_rpc_failover_events (endpoint, created_at DESC);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('025_production_resilience_node_failover')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
