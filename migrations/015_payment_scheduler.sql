BEGIN;

CREATE TABLE IF NOT EXISTS seymour_engine.payment_scheduler_profiles (
    scheduler_profile_id UUID PRIMARY KEY,
    pool_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    source_wallet_id UUID NOT NULL REFERENCES seymour_engine.wallets(wallet_id) ON DELETE RESTRICT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    schedule_type TEXT NOT NULL DEFAULT 'daily',
    schedule_hour SMALLINT,
    schedule_weekday SMALLINT,
    schedule_monthday SMALLINT,
    minimum_payout NUMERIC(28, 12) NOT NULL,
    absolute_minimum NUMERIC(28, 12) NOT NULL DEFAULT 0,
    maximum_payout NUMERIC(28, 12),
    maximum_behavior TEXT NOT NULL DEFAULT 'pay_full',
    retry_limit INTEGER NOT NULL DEFAULT 3,
    retry_backoff_seconds INTEGER NOT NULL DEFAULT 300,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_payment_scheduler_profile UNIQUE (pool_id, coin, network),
    CONSTRAINT ck_payment_scheduler_schedule CHECK (
        schedule_type IN ('immediate', 'hourly', 'daily', 'weekly', 'monthly', 'manual')
    ),
    CONSTRAINT ck_payment_scheduler_limits CHECK (
        minimum_payout >= 0 AND absolute_minimum >= 0 AND
        (maximum_payout IS NULL OR maximum_payout > 0) AND
        retry_limit >= 0 AND retry_backoff_seconds >= 0
    ),
    CONSTRAINT ck_payment_scheduler_calendar CHECK (
        (schedule_hour IS NULL OR schedule_hour BETWEEN 0 AND 23) AND
        (schedule_weekday IS NULL OR schedule_weekday BETWEEN 0 AND 6) AND
        (schedule_monthday IS NULL OR schedule_monthday BETWEEN 1 AND 28)
    ),
    CONSTRAINT ck_payment_scheduler_maximum_behavior CHECK (
        maximum_behavior IN ('pay_full', 'cap_and_carry')
    )
);

CREATE INDEX IF NOT EXISTS idx_payment_scheduler_profiles_due
    ON seymour_engine.payment_scheduler_profiles (enabled, next_run_at);

CREATE TABLE IF NOT EXISTS seymour_engine.worker_payment_policies (
    worker_payment_policy_id UUID PRIMARY KEY,
    worker_id UUID NOT NULL REFERENCES seymour_engine.workers(worker_id) ON DELETE CASCADE,
    coin TEXT NOT NULL,
    network TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    minimum_payout NUMERIC(28, 12),
    schedule_type TEXT,
    destination_wallet_id UUID REFERENCES seymour_engine.wallets(wallet_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT uq_worker_payment_policy UNIQUE (worker_id, coin, network),
    CONSTRAINT ck_worker_payment_policy_minimum CHECK (
        minimum_payout IS NULL OR minimum_payout >= 0
    ),
    CONSTRAINT ck_worker_payment_policy_schedule CHECK (
        schedule_type IS NULL OR schedule_type IN (
            'immediate', 'hourly', 'daily', 'weekly', 'monthly', 'manual'
        )
    )
);

CREATE TABLE IF NOT EXISTS seymour_engine.payment_scheduler_runs (
    scheduler_run_id UUID PRIMARY KEY,
    scheduler_profile_id UUID NOT NULL REFERENCES seymour_engine.payment_scheduler_profiles(scheduler_profile_id) ON DELETE CASCADE,
    run_key TEXT NOT NULL UNIQUE,
    trigger_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    actor TEXT NOT NULL,
    lock_token UUID NOT NULL,
    eligible_count INTEGER NOT NULL DEFAULT 0,
    payout_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    total_amount NUMERIC(28, 12) NOT NULL DEFAULT 0,
    failure_reason TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    retry_of_run_id UUID REFERENCES seymour_engine.payment_scheduler_runs(scheduler_run_id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT ck_payment_scheduler_run_trigger CHECK (
        trigger_type IN ('scheduled', 'manual', 'retry')
    ),
    CONSTRAINT ck_payment_scheduler_run_status CHECK (
        status IN ('running', 'completed', 'failed', 'cancelled', 'skipped')
    ),
    CONSTRAINT ck_payment_scheduler_run_counts CHECK (
        eligible_count >= 0 AND payout_count >= 0 AND skipped_count >= 0 AND
        failed_count >= 0 AND total_amount >= 0
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_scheduler_active_run
    ON seymour_engine.payment_scheduler_runs (scheduler_profile_id)
    WHERE status = 'running';

CREATE INDEX IF NOT EXISTS idx_payment_scheduler_runs_history
    ON seymour_engine.payment_scheduler_runs (scheduler_profile_id, started_at DESC);

CREATE TABLE IF NOT EXISTS seymour_engine.payment_scheduler_jobs (
    scheduler_job_id UUID PRIMARY KEY,
    scheduler_run_id UUID NOT NULL REFERENCES seymour_engine.payment_scheduler_runs(scheduler_run_id) ON DELETE CASCADE,
    worker_id UUID REFERENCES seymour_engine.workers(worker_id) ON DELETE SET NULL,
    payout_batch_id UUID REFERENCES seymour_engine.payout_batches(payout_batch_id) ON DELETE SET NULL,
    pool_id TEXT NOT NULL,
    miner TEXT NOT NULL,
    worker TEXT NOT NULL DEFAULT '',
    destination_address TEXT NOT NULL,
    eligible_balance NUMERIC(28, 12) NOT NULL,
    threshold_amount NUMERIC(28, 12) NOT NULL,
    payout_amount NUMERIC(28, 12) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payment_scheduler_job_worker UNIQUE (scheduler_run_id, pool_id, miner, worker),
    CONSTRAINT ck_payment_scheduler_job_status CHECK (
        status IN ('pending', 'batched', 'completed', 'failed', 'retry_wait', 'cancelled', 'skipped')
    ),
    CONSTRAINT ck_payment_scheduler_job_amounts CHECK (
        eligible_balance >= 0 AND threshold_amount >= 0 AND payout_amount > 0 AND attempt_count >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_payment_scheduler_jobs_retry
    ON seymour_engine.payment_scheduler_jobs (status, next_attempt_at);

CREATE TABLE IF NOT EXISTS seymour_engine.payment_scheduler_events (
    scheduler_event_id UUID PRIMARY KEY,
    scheduler_run_id UUID REFERENCES seymour_engine.payment_scheduler_runs(scheduler_run_id) ON DELETE CASCADE,
    scheduler_job_id UUID REFERENCES seymour_engine.payment_scheduler_jobs(scheduler_job_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_payment_scheduler_event_target CHECK (
        scheduler_run_id IS NOT NULL OR scheduler_job_id IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_payment_scheduler_events_run_time
    ON seymour_engine.payment_scheduler_events (scheduler_run_id, created_at);

INSERT INTO seymour_engine.schema_migrations (migration_id)
VALUES ('015_payment_scheduler')
ON CONFLICT (migration_id) DO NOTHING;

COMMIT;
