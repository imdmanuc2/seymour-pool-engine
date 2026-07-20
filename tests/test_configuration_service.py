from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from seymour_pool_engine.services.configuration_service import ConfigurationService


class FakeRepository:
    def __init__(self) -> None:
        self.rows = {}
        self.validations = []
        self.exports = []
        self.imports = []

    def record_validation(self, **values):
        self.validations.append(values)

    def upsert_profile_revision(self, **values):
        previous = self.rows.get(values["profile_key"], [])
        row = {
            "profile_key": values["profile_key"],
            "domain": values["domain"],
            "revision_number": len(previous) + 1,
            "configuration": deepcopy(values["configuration"]),
            "checksum": values["checksum"],
            "status": "active",
            "change_summary": values["change_summary"],
            "changed_by": values["changed_by"],
            "created_at": datetime.now(UTC),
        }
        previous.append(row)
        self.rows[values["profile_key"]] = previous
        return row

    def get_active(self, *, profile_key):
        rows = self.rows.get(profile_key, [])
        return rows[-1] if rows else None

    def list_active(self):
        return [rows[-1] for rows in self.rows.values()]

    def history(self, *, profile_key):
        return list(reversed(self.rows.get(profile_key, [])))

    def rollback(self, *, profile_key, revision_number, changed_by):
        rows = self.rows.get(profile_key, [])
        target = next((r for r in rows if r["revision_number"] == revision_number), None)
        if target is None:
            return None
        return self.upsert_profile_revision(
            profile_key=profile_key,
            domain=target["domain"],
            configuration=target["configuration"],
            checksum=target["checksum"],
            change_summary=f"Rollback to revision {revision_number}",
            changed_by=changed_by,
        )

    def record_export(self, *, checksum, profile_count, actor):
        value = uuid4()
        self.exports.append((checksum, profile_count, actor))
        return value

    def record_import(self, **values):
        value = uuid4()
        self.imports.append(values)
        return value


def test_developer_fee_cannot_be_disabled_or_lowered():
    service = ConfigurationService(FakeRepository())
    result = service.validate(
        profile_key="fees.btc",
        domain="developer-fee",
        configuration={"enabled": False, "percent": 0.5},
    )
    assert result["valid"] is False
    assert any("disabled" in error for error in result["errors"])
    assert any("0.75" in error for error in result["errors"])


def test_configuration_revisions_and_rollback():
    service = ConfigurationService(FakeRepository())
    first = service.put(
        profile_key="pool.btc",
        domain="pool",
        configuration={"poolId": "btc"},
        change_summary="Initial",
        changed_by="test",
    )
    second = service.put(
        profile_key="pool.btc",
        domain="pool",
        configuration={"poolId": "btc", "name": "Seymour BTC"},
        change_summary="Name",
        changed_by="test",
    )
    rolled_back = service.rollback(
        profile_key="pool.btc", revision_number=1, changed_by="test"
    )
    assert first["revisionNumber"] == 1
    assert second["revisionNumber"] == 2
    assert rolled_back["revisionNumber"] == 3
    assert rolled_back["configuration"] == {"poolId": "btc"}


def test_export_import_checksum_integrity():
    source = ConfigurationService(FakeRepository())
    source.put(
        profile_key="coin.btc",
        domain="coin",
        configuration={"symbol": "BTC"},
        change_summary="Initial",
        changed_by="test",
    )
    backup = source.export(actor="test")
    target = ConfigurationService(FakeRepository())
    result = target.import_backup(
        payload=backup["payload"], checksum=backup["checksum"], actor="test"
    )
    assert result["importedProfiles"] == 1
    assert target.get(profile_key="coin.btc")["configuration"]["symbol"] == "BTC"
    with pytest.raises(ValueError, match="checksum mismatch"):
        target.import_backup(
            payload=backup["payload"], checksum="bad-checksum", actor="test"
        )
