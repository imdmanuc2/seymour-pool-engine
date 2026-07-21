from datetime import UTC, datetime
from uuid import uuid4

import pytest

from seymour_pool_engine.services.security_service import SecurityService


class Repo:
    def __init__(self):
        self.principal_id = uuid4()
        self.raw_hash = None
        self.permissions = ["pool.read"]

    def create_principal(self, **values):
        return {"principal_id": self.principal_id, **values, "created_at": datetime.now(UTC)}

    def list_principals(self):
        return []

    def list_roles(self):
        return [{"role_id": uuid4(), "role_name": "operator"}]

    def get_principal(self, principal_id):
        return {"principal_id": principal_id, "principal_name": "nexus"}

    def grant_role(self, principal_id, role_name, granted_by):
        return {"principal_id": principal_id, "role_id": uuid4(), "granted_by": granted_by}

    def permissions_for_principal(self, principal_id):
        return self.permissions

    def create_api_key(self, **values):
        self.raw_hash = values["key_hash"]
        return {"api_key_id": uuid4(), **values}

    def find_active_api_key(self, key_hash):
        if key_hash != self.raw_hash:
            return None
        return {
            "api_key_id": uuid4(),
            "principal_id": self.principal_id,
            "principal_type": "service",
            "principal_name": "nexus",
        }

    def touch_api_key(self, api_key_id):
        return None

    def revoke_api_key(self, api_key_id):
        return {"api_key_id": api_key_id, "revoked_at": datetime.now(UTC)}

    def list_events(self, limit):
        return []


def test_password_hash_round_trip():
    encoded = SecurityService.hash_password("correct horse battery staple")
    assert SecurityService.verify_password("correct horse battery staple", encoded)
    assert not SecurityService.verify_password("wrong password", encoded)


def test_rejects_short_user_password():
    with pytest.raises(ValueError, match="at least 12"):
        SecurityService(Repo()).create_principal(
            principal_type="user", principal_name="alice", password="short"
        )


def test_service_identity_can_issue_and_authenticate_api_key():
    repo = Repo()
    service = SecurityService(repo)
    created = service.issue_api_key(principal_id=repo.principal_id, key_name="nexus")
    assert created["apiKey"].startswith("spe_")
    identity = service.authenticate_api_key(created["apiKey"])
    assert identity["principalName"] == "nexus"
    assert identity["permissions"] == ["pool.read"]


def test_authorization_denies_missing_permission():
    repo = Repo()
    service = SecurityService(repo)
    created = service.issue_api_key(principal_id=repo.principal_id, key_name="nexus")
    with pytest.raises(PermissionError, match="wallet.manage"):
        service.authorize(created["apiKey"], "wallet.manage")


def test_principal_response_redacts_password_hash():
    result = SecurityService(Repo()).create_principal(
        principal_type="service", principal_name="Nexus", password=None
    )
    assert result["principalName"] == "nexus"
    assert "passwordHash" not in result
