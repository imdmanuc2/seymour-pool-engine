from uuid import uuid4

from seymour_pool_engine.testing.synthetic_rewards import synthetic_reward_request


def test_synthetic_reward_request_is_valid() -> None:
    request = synthetic_reward_request(uuid4())
    assert request["gross_reward"] > 0
    assert request["start_at"] < request["end_at"]
