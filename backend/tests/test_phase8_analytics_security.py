from app.security.clerk import ROLE_PERMISSIONS
from app.security.tenant import TenantContext
import pytest


def test_governed_export_is_not_available_to_viewers_or_staff():
    assert "analytics:export" not in ROLE_PERMISSIONS["org:viewer"]
    assert "analytics:export" not in ROLE_PERMISSIONS["org:staff"]
    assert "analytics:export" in ROLE_PERMISSIONS["org:manager"]
    assert "analytics:export" in ROLE_PERMISSIONS["org:admin"]
    assert "analytics:export" in ROLE_PERMISSIONS["org:owner"]


def test_compliance_trace_requires_compliance_permission():
    viewer=TenantContext("org-a","user-a",frozenset({"analytics:read"}),"org:viewer")
    with pytest.raises(Exception): viewer.require("compliance:read")
