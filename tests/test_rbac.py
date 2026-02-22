"""
Module 2 – app.core.rbac   (Priority 1 – Privilege escalation risk)

Tests cover:
  • require_role factory with single / multiple allowed roles
  • 403 when role is not in the allow-list
  • Returned user dict integrity
"""

import os
import sys

import pytest
from fastapi import HTTPException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.rbac import require_role


class TestRequireRoleSingle:

    def test_admin_allowed(self):
        fn = require_role("admin")
        user = {"id": 1, "username": "alice", "role": "admin"}
        assert fn(user) is user

    def test_user_denied(self):
        fn = require_role("admin")
        user = {"id": 2, "username": "bob", "role": "user"}
        with pytest.raises(HTTPException) as exc:
            fn(user)
        assert exc.value.status_code == 403
        assert "Insufficient permissions" in exc.value.detail


class TestRequireRoleMultiple:

    def test_any_listed_role_passes(self):
        fn = require_role("admin", "user")
        assert fn({"id": 1, "username": "a", "role": "user"})["role"] == "user"
        assert fn({"id": 2, "username": "b", "role": "admin"})["role"] == "admin"

    def test_unlisted_role_denied(self):
        fn = require_role("admin", "moderator")
        with pytest.raises(HTTPException) as exc:
            fn({"id": 3, "username": "c", "role": "user"})
        assert exc.value.status_code == 403


class TestRequireRoleReturnValue:

    def test_returns_full_user_dict(self):
        fn = require_role("user")
        user = {"id": 10, "username": "eve", "role": "user"}
        result = fn(user)
        assert result["id"] == 10
        assert result["username"] == "eve"
        assert result["role"] == "user"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))