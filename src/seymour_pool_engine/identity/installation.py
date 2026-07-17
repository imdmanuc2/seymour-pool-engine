import uuid
from pathlib import Path

from seymour_pool_engine.config import get_settings


def _read_identity(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None

    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _write_identity(path: Path, installation_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{installation_id}\n", encoding="utf-8")


def get_or_create_installation_id() -> str:
    """
    Return a persistent installation UUID.

    An explicitly configured instance ID wins. Otherwise, the UUID is stored
    in the configured identity file and survives restarts and address changes.
    """

    settings = get_settings()

    if settings.instance_id:
        return settings.instance_id.strip()

    existing = _read_identity(settings.identity_file)
    if existing:
        return existing

    installation_id = str(uuid.uuid4())
    _write_identity(settings.identity_file, installation_id)
    return installation_id
