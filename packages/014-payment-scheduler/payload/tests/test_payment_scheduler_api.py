from seymour_pool_engine.main import app


def test_payment_scheduler_routes_are_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/payment-scheduler/profiles",
        "/api/v1/payment-scheduler/worker-policies",
        "/api/v1/payment-scheduler/run-due",
        "/api/v1/payment-scheduler/profiles/{scheduler_profile_id}/run",
        "/api/v1/payment-scheduler/runs",
        "/api/v1/payment-scheduler/jobs",
        "/api/v1/payment-scheduler/jobs/{scheduler_job_id}/retry",
        "/api/v1/payment-scheduler/jobs/{scheduler_job_id}/cancel",
    }
    assert not required - paths
