from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def test_artifacts():
 required=[ROOT/'.env.production.example',ROOT/'packaging/systemd/seymour-pool-engine-api.service',ROOT/'packaging/systemd/seymour-pool-engine-stratum.service',ROOT/'scripts/production/install-production.sh',ROOT/'scripts/production/preflight.sh',ROOT/'docs/00-START-HERE.md',ROOT/'docs/06-CKPOOL-LIVE-CUTOVER.md']
 assert all(p.is_file() for p in required)
def test_safe_parallel_default(): assert 'SEYMOUR_STRATUM_PORT=3334' in (ROOT/'.env.production.example').read_text()
def test_installer_does_not_stop_ckpool():
 t=(ROOT/'scripts/production/install-production.sh').read_text().lower(); assert 'systemctl stop ckpool' not in t and 'systemctl disable ckpool' not in t
def test_safe_payout_required(): assert 'SEYMOUR_BITCOIN_PAYOUT_SCRIPT=CHANGE_ME' in (ROOT/'.env.production.example').read_text()
def test_rollback_preserves_ckpool(): assert 'ckpool configuration was not changed' in (ROOT/'scripts/production/rollback-to-ckpool.sh').read_text().lower()
