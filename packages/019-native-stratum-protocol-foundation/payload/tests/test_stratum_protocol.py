import pytest

from seymour_pool_engine.engines.protocol.codec import (
    ProtocolError,
    decode_request,
    encode,
)


def test_decode_request() -> None:
    request = decode_request(b'{"id":1,"method":"mining.subscribe","params":["miner"]}\n')
    assert request.request_id == 1
    assert request.method == "mining.subscribe"


def test_invalid_json() -> None:
    with pytest.raises(ProtocolError):
        decode_request(b"bad\n")


def test_encode_line_delimited() -> None:
    assert encode({"id": 1}).endswith(b"\n")
