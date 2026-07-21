BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.security_principals (
    principal_id UUID PRIMARY KEY,
    principal_type TEXT NOT NULL CHECK (principal_type IN ('user','service')),
    principal_name TEXT NOT NULL,
    display_name TEXT,
    email TEXT,
    password_hash TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','locked')),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_authenticated_at TIMESTAMPTZ,
    CONSTRAINT uq_security_principal_name UNIQUE (principal_type, principal_name)
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_roles (
    role_id UUID PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT,
    system_role BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_permissions (
    permission_id UUID PRIMARY KEY,
    permission_name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_role_permissions (
    role_id UUID NOT NULL REFERENCES seymour_engine.security_roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES seymour_engine.security_permissions(permission_id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by TEXT NOT NULL,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_principal_roles (
    principal_id UUID NOT NULL REFERENCES seymour_engine.security_principals(principal_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES seymour_engine.security_roles(role_id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by TEXT NOT NULL,
    PRIMARY KEY (principal_id, role_id)
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_api_keys (
    api_key_id UUID PRIMARY KEY,
    principal_id UUID NOT NULL REFERENCES seymour_engine.security_principals(principal_id) ON DELETE CASCADE,
    key_name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_security_api_key_name UNIQUE (principal_id, key_name)
);
CREATE INDEX IF NOT EXISTS idx_security_api_keys_prefix ON seymour_engine.security_api_keys(key_prefix);

CREATE TABLE IF NOT EXISTS seymour_engine.security_sessions (
    session_id UUID PRIMARY KEY,
    principal_id UUID NOT NULL REFERENCES seymour_engine.security_principals(principal_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    client_ip TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_security_sessions_active ON seymour_engine.security_sessions(principal_id, expires_at) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS seymour_engine.security_events (
    security_event_id UUID PRIMARY KEY,
    principal_id UUID REFERENCES seymour_engine.security_principals(principal_id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('success','denied','failure')),
    actor TEXT NOT NULL,
    resource TEXT,
    client_ip TEXT,
    correlation_id TEXT,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_security_events_created ON seymour_engine.security_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_principal ON seymour_engine.security_events(principal_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.security_rate_limit_policies (
    rate_limit_policy_id UUID PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    principal_type TEXT CHECK (principal_type IN ('user','service')),
    requests_per_minute INTEGER NOT NULL CHECK (requests_per_minute > 0),
    burst_size INTEGER NOT NULL CHECK (burst_size > 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS seymour_engine.security_approval_requests (
    approval_request_id UUID PRIMARY KEY,
    requested_by UUID REFERENCES seymour_engine.security_principals(principal_id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','denied','cancelled','expired')),
    reason TEXT,
    expires_at TIMESTAMPTZ,
    decided_by UUID REFERENCES seymour_engine.security_principals(principal_id) ON DELETE SET NULL,
    decided_at TIMESTAMPTZ,
    decision_note TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_security_approvals_status ON seymour_engine.security_approval_requests(status, created_at DESC);

INSERT INTO seymour_engine.security_permissions(permission_id, permission_name, description)
VALUES
(gen_random_uuid(),'security.read','View security configuration and audit events'),
(gen_random_uuid(),'security.manage','Manage principals, roles, permissions, and credentials'),
(gen_random_uuid(),'pool.read','View pool operations'),
(gen_random_uuid(),'pool.operate','Execute pool operations'),
(gen_random_uuid(),'wallet.read','View wallet state'),
(gen_random_uuid(),'wallet.manage','Manage wallet operations'),
(gen_random_uuid(),'payout.approve','Approve payout operations')
ON CONFLICT (permission_name) DO NOTHING;

INSERT INTO seymour_engine.security_roles(role_id, role_name, description, system_role)
VALUES
(gen_random_uuid(),'administrator','Full Seymour Pool Engine administration',TRUE),
(gen_random_uuid(),'operator','Operate pools and view financial state',TRUE),
(gen_random_uuid(),'auditor','Read-only operational and security access',TRUE),
(gen_random_uuid(),'nexus-service','Service identity used by Nexus integrations',TRUE)
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO seymour_engine.security_role_permissions(role_id, permission_id, granted_by)
SELECT r.role_id, p.permission_id, 'migration-017'
FROM seymour_engine.security_roles r CROSS JOIN seymour_engine.security_permissions p
WHERE r.role_name='administrator'
ON CONFLICT DO NOTHING;

INSERT INTO seymour_engine.security_role_permissions(role_id, permission_id, granted_by)
SELECT r.role_id, p.permission_id, 'migration-017'
FROM seymour_engine.security_roles r JOIN seymour_engine.security_permissions p
ON p.permission_name IN ('security.read','pool.read','pool.operate','wallet.read')
WHERE r.role_name='operator'
ON CONFLICT DO NOTHING;

INSERT INTO seymour_engine.security_role_permissions(role_id, permission_id, granted_by)
SELECT r.role_id, p.permission_id, 'migration-017'
FROM seymour_engine.security_roles r JOIN seymour_engine.security_permissions p
ON p.permission_name IN ('security.read','pool.read','wallet.read')
WHERE r.role_name='auditor'
ON CONFLICT DO NOTHING;

INSERT INTO seymour_engine.security_role_permissions(role_id, permission_id, granted_by)
SELECT r.role_id, p.permission_id, 'migration-017'
FROM seymour_engine.security_roles r JOIN seymour_engine.security_permissions p
ON p.permission_name IN ('pool.read','pool.operate','wallet.read','wallet.manage')
WHERE r.role_name='nexus-service'
ON CONFLICT DO NOTHING;

INSERT INTO seymour_engine.security_rate_limit_policies(
    rate_limit_policy_id, policy_name, requests_per_minute, burst_size
) VALUES (gen_random_uuid(),'default-authenticated',600,100)
ON CONFLICT (policy_name) DO NOTHING;

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('017_security_access_control')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
