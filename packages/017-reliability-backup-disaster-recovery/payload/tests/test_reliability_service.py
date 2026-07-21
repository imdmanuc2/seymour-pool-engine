from pathlib import Path
from uuid import uuid4

import pytest

from seymour_pool_engine.services.reliability_service import ReliabilityService


class FakeRepository:
    def __init__(self):
        self.profile = {"backup_profile_id": uuid4(), "profile_key": "daily-db", "enabled": True}
        self.checks = []

    def list_profiles(self):
        return [self.profile]

    def get_profile(self, key):
        return self.profile if key == "daily-db" else None

    def create_run(self, profile_id, target_id, requested_by, metadata):
        return {
            "backup_run_id": uuid4(),
            "backup_profile_id": profile_id,
            "backup_target_id": target_id,
            "status": "queued",
            "requested_by": requested_by,
            "metadata": metadata,
        }

    def record_integrity_check(self, **values):
        self.checks.append(values)
        return {"backup_integrity_check_id": uuid4(), **values}

    def create_restore_run(self, **values):
        return {"restore_run_id": uuid4(), "status": "queued", **values}


def test_sha256_and_integrity_check(tmp_path: Path):
    artifact = tmp_path / "backup.dump"
    artifact.write_bytes(b"seymour")
    repo = FakeRepository()
    service = ReliabilityService(repo)
    checksum = service.sha256_file(artifact)
    result = service.verify_artifact(
        backup_artifact_id=uuid4(),
        path=str(artifact),
        expected_checksum=checksum,
        checked_by="test",
    )
    assert result["status"] == "passed"
    assert repo.checks[0]["observed_checksum"] == checksum


def test_backup_and_restore_guards():
    service = ReliabilityService(FakeRepository())
    run = service.request_backup(profile_key="daily-db", target_id=uuid4(), requested_by="test")
    assert run["status"] == "queued"
    with pytest.raises(ValueError, match="approval"):
        service.request_restore(
            backup_run_id=uuid4(),
            mode="restore",
            requested_by="test",
            target_environment="production",
        )
    assert service.database_backup_command("/tmp/a.dump")[0] == "pg_dump"
