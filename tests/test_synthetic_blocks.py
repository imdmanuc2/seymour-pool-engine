from datetime import UTC, datetime

from seymour_pool_engine.testing.synthetic_blocks import generate_synthetic_blocks


def test_synthetic_blocks_are_deterministic() -> None:
    end = datetime(2026, 7, 20, tzinfo=UTC)
    first = generate_synthetic_blocks(count=8, seed=42, end=end)
    second = generate_synthetic_blocks(count=8, seed=42, end=end)
    assert first == second
    assert {item["status"] for item in first} == {
        "candidate",
        "immature",
        "confirmed",
        "orphaned",
    }
