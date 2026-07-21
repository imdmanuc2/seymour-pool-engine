import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.reliability_repository import ReliabilityRepository


class ReliabilityService:
    def __init__(self, repository: ReliabilityRepository | None = None):
        self.repository = repository or ReliabilityRepository()

    def profiles(self) -> list[dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.list_profiles()]

    def put_profile(self, **values: Any) -> dict[str, Any]:
        if values["backup_type"] not in {"database", "configuration", "wallet_metadata", "full"}:
            raise ValueError("Unsupported backup type")
        if values.get("retention_days", 30) < 1:
            raise ValueError("Retention days must be at least 1")
        return self._serialize(self.repository.upsert_profile(**values))

    def targets(self) -> list[dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.list_targets()]

    def put_target(self, **values: Any) -> dict[str, Any]:
        if values["target_type"] not in {"filesystem", "object_storage", "remote_host"}:
            raise ValueError("Unsupported backup target type")
        if not values["location"].strip():
            raise ValueError("Backup target location is required")
        return self._serialize(self.repository.upsert_target(**values))

    def request_backup(
        self,
        *,
        profile_key: str,
        target_id: UUID,
        requested_by: str = "api",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = self.repository.get_profile(profile_key)
        if not profile or not profile["enabled"]:
            raise ValueError("Backup profile does not exist or is disabled")
        row = self.repository.create_run(
            profile["backup_profile_id"], target_id, requested_by, metadata or {}
        )
        return self._serialize(row)

    def runs(self, limit: int = 100) -> list[dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.list_runs(max(1, min(limit, 500)))]

    def register_artifact(self, *, path: str, **values: Any) -> dict[str, Any]:
        artifact = Path(path)
        if not artifact.is_file():
            raise ValueError("Backup artifact does not exist")
        digest = self.sha256_file(artifact)
        row = self.repository.record_artifact(
            relative_path=path, size_bytes=artifact.stat().st_size, sha256_checksum=digest, **values
        )
        return self._serialize(row)

    def verify_artifact(
        self,
        *,
        backup_artifact_id: UUID,
        path: str,
        expected_checksum: str,
        checked_by: str = "api",
    ) -> dict[str, Any]:
        artifact = Path(path)
        observed = self.sha256_file(artifact) if artifact.is_file() else None
        status = "passed" if observed == expected_checksum else "failed"
        row = self.repository.record_integrity_check(
            backup_artifact_id=backup_artifact_id,
            status=status,
            expected_checksum=expected_checksum,
            observed_checksum=observed,
            checked_by=checked_by,
            details={"path": path},
        )
        return self._serialize(row)

    def request_restore(
        self, *, backup_run_id: UUID, mode: str, requested_by: str, target_environment: str
    ) -> dict[str, Any]:
        if mode not in {"validate", "restore"}:
            raise ValueError("Restore mode must be validate or restore")
        if mode == "restore" and target_environment.lower() == "production":
            raise ValueError("Production restore requires an external approval workflow")
        return self._serialize(
            self.repository.create_restore_run(
                backup_run_id=backup_run_id,
                mode=mode,
                requested_by=requested_by,
                target_environment=target_environment,
            )
        )

    def playbooks(self) -> list[dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.list_playbooks()]

    @staticmethod
    def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def database_backup_command(output_path: str) -> list[str]:
        return ["pg_dump", "--format=custom", "--no-owner", "--no-acl", "--file", output_path]

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in row.items():
            camel = key.split("_")[0] + "".join(part.title() for part in key.split("_")[1:])
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.astimezone(UTC).isoformat()
            result[camel] = value
        return result
