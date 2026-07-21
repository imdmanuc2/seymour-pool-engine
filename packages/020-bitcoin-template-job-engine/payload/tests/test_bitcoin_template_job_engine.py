from seymour_pool_engine.engines.jobs.bitcoin import (
    build_coinbase_parts,
    build_merkle_branches,
    create_stratum_job,
)
from seymour_pool_engine.engines.jobs.models import BitcoinBlockTemplate


def sample_template() -> BitcoinBlockTemplate:
    return BitcoinBlockTemplate.from_rpc(
        {
            "height": 900001,
            "previousblockhash": "11" * 32,
            "version": 0x20000000,
            "bits": "170fffff",
            "curtime": 1753100000,
            "mintime": 1753099900,
            "coinbasevalue": 312500000,
            "target": "00" * 32,
            "workid": "work-1",
            "transactions": [
                {"txid": "22" * 32, "hash": "33" * 32, "data": "00", "fee": 1000}
            ],
        }
    )


def test_template_parsing() -> None:
    template = sample_template()
    assert template.height == 900001
    assert template.coinbase_value == 312500000
    assert len(template.transactions) == 1


def test_coinbase_parts_leave_extranonce_gap() -> None:
    coinbase1, coinbase2 = build_coinbase_parts(sample_template(), "51", 6, 4)
    assert bytes.fromhex(coinbase1)
    assert bytes.fromhex(coinbase2)
    assert coinbase2.endswith("00000000")


def test_merkle_branch_is_created_for_template_transaction() -> None:
    branches = build_merkle_branches(["33" * 32])
    assert branches == ("33" * 32,)


def test_stratum_job_notify_shape() -> None:
    job = create_stratum_job(sample_template(), "51")
    params = job.notify_params()
    assert len(params) == 9
    assert params[1] == "11" * 32
    assert params[5] == "20000000"
    assert params[6] == "170fffff"
    assert job.source == "bitcoin-rpc"
    assert job.transaction_count == 1
