from seymour_pool_engine.engines.protocol.codec import decode_request
from seymour_pool_engine.engines.session.models import StratumSession
from seymour_pool_engine.stratum.dispatcher import (
    SUPPORTED_VERSION_ROLLING_MASK,
    StratumDispatcher,
)


class ConfigureRepository:
    pass


def make_session() -> StratumSession:
    return StratumSession(
        remote_host="192.168.1.151",
        remote_port=40000,
        extranonce1="00000001",
        extranonce2_size=4,
        difficulty=1.0,
    )


def configure_request(
    *,
    request_id: int = 1,
    mask: str = "ffffffff",
    extensions: list[str] | None = None,
):
    extensions = extensions or ["version-rolling"]
    payload = (
        "{"
        f'"id":{request_id},'
        '"method":"mining.configure",'
        f'"params":[{extensions!r},{{"version-rolling.mask":"{mask}"}}]'
        "}"
    ).replace("'", '"')

    return decode_request(payload.encode() + b"\n", 4096)


def test_version_rolling_negotiates_supported_mask() -> None:
    session = make_session()
    dispatcher = StratumDispatcher(ConfigureRepository())

    result = dispatcher.dispatch(session, configure_request())

    message = result.messages[0]

    assert result.error is None
    assert message["id"] == 1
    assert message["error"] is None
    assert message["result"]["version-rolling"] is True
    assert message["result"]["version-rolling.mask"] == "1fffe000"
    assert session.version_rolling is True
    assert session.version_rolling_mask == "1fffe000"


def test_version_rolling_intersects_requested_mask() -> None:
    session = make_session()
    dispatcher = StratumDispatcher(ConfigureRepository())

    result = dispatcher.dispatch(
        session,
        configure_request(mask="0000e000"),
    )

    assert result.messages[0]["result"]["version-rolling"] is True
    assert result.messages[0]["result"]["version-rolling.mask"] == "0000e000"
    assert session.version_rolling_mask == "0000e000"


def test_invalid_version_rolling_mask_is_rejected_safely() -> None:
    session = make_session()
    dispatcher = StratumDispatcher(ConfigureRepository())

    result = dispatcher.dispatch(
        session,
        configure_request(mask="not-hex"),
    )

    assert result.messages[0]["result"]["version-rolling"] is False
    assert "version-rolling.mask" not in result.messages[0]["result"]
    assert session.version_rolling is False
    assert session.version_rolling_mask is None


def test_unknown_extensions_remain_disabled() -> None:
    session = make_session()
    dispatcher = StratumDispatcher(ConfigureRepository())

    result = dispatcher.dispatch(
        session,
        configure_request(
            extensions=["version-rolling", "minimum-difficulty"],
        ),
    )

    response_result = result.messages[0]["result"]

    assert response_result["version-rolling"] is True
    assert response_result["minimum-difficulty"] is False
    assert int(response_result["version-rolling.mask"], 16) == (
        0xFFFFFFFF & SUPPORTED_VERSION_ROLLING_MASK
    )
