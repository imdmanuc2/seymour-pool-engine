import httpx
import pytest

from seymour_pool_engine.providers.bitcoin.rpc import BitcoinRpcClient, BitcoinRpcError


def test_getblocktemplate_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"result": {"height": 1}, "error": None}

    def fake_post(url, **kwargs):
        seen.update({"url": url, **kwargs})
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    result = BitcoinRpcClient("http://node:8332", "rpc", "secret").get_block_template()
    assert result == {"height": 1}
    assert seen["json"]["method"] == "getblocktemplate"
    assert seen["auth"] == ("rpc", "secret")


def test_rpc_error_is_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"result": None, "error": {"code": -10, "message": "not ready"}}

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())
    with pytest.raises(BitcoinRpcError):
        BitcoinRpcClient("http://node:8332").get_block_template()
