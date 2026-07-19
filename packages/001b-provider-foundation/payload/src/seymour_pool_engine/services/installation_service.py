import logging
import socket

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.identity import get_or_create_installation_id
from seymour_pool_engine.repositories.installation_repository import InstallationRepository

logger = logging.getLogger(__name__)


def register_installation() -> dict | None:
    settings = get_settings()
    try:
        return InstallationRepository().register(
            installation_id=get_or_create_installation_id(),
            display_name=settings.display_name,
            environment=settings.environment,
            hostname=socket.gethostname(),
            engine_version=settings.version,
            provider_name="miningcore",
        )
    except Exception:
        logger.exception("Installation registration failed")
        return None
