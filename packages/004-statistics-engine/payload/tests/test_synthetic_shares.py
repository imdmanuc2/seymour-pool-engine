from datetime import UTC, datetime

from seymour_pool_engine.testing import generate_synthetic_shares


def test_synthetic_shares_are_repeatable() -> None:
    end = datetime(2026, 1, 1, tzinfo=UTC)
    first = generate_synthetic_shares(workers=3, shares_per_worker=4, seed=42, end_at=end)
    second = generate_synthetic_shares(workers=3, shares_per_worker=4, seed=42, end_at=end)
    assert len(first) == 12
    assert [share.model_dump() for share in first] == [share.model_dump() for share in second]
