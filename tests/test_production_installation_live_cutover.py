from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_artifacts():
    required = [
        ROOT / ".env.production.example",
        ROOT / "packaging/systemd/seymour-pool-engine-api.service",
        ROOT / "packaging/systemd/seymour-pool-engine-stratum.service",
        ROOT / "scripts/production/install-production.sh",
        ROOT / "scripts/production/rollback-to-ckpool.sh",
    ]

    assert all(path.is_file() for path in required)


def test_safe_parallel_default():
    text = (ROOT / ".env.production.example").read_text()
    assert "SEYMOUR_STRATUM_PORT=3334" in text


def test_installer_does_not_stop_ckpool():
    text = (
        ROOT / "scripts/production/install-production.sh"
    ).read_text().lower()

    assert "systemctl stop ckpool" not in text
    assert "systemctl disable ckpool" not in text


def test_safe_payout_required():
    text = (ROOT / ".env.production.example").read_text()
    assert "SEYMOUR_BITCOIN_PAYOUT_SCRIPT=CHANGE_ME" in text


def test_rollback_preserves_ckpool():
    text = (
        ROOT / "scripts/production/rollback-to-ckpool.sh"
    ).read_text().lower()

    assert "ckpool configuration was not changed" in text