from seymour_pool_engine.config.settings import get_settings
from seymour_pool_engine.providers.bitcoin.resilience import ResilientBitcoinRpcClient


def configured_rpc_urls() -> list[str]:
    settings = get_settings()
    raw = settings.bitcoin_rpc_urls or settings.bitcoin_rpc_url
    return [part.strip() for part in raw.split(",") if part.strip()]


def create_bitcoin_rpc_client() -> ResilientBitcoinRpcClient:
    settings = get_settings()
    return ResilientBitcoinRpcClient(
        configured_rpc_urls(),
        settings.bitcoin_rpc_user,
        settings.bitcoin_rpc_password,
        settings.bitcoin_rpc_timeout_seconds,
        settings.bitcoin_rpc_failure_threshold,
        settings.bitcoin_rpc_cooldown_seconds,
    )
