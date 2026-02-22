"""
Module 1 – app.core.security   (Priority 1 – Auth bypass risk)

Tests cover:
  • hash_password / verify_password
  • create_access_token / decode_token
  • get_current_user
  • require_roles
"""

import os
import sys

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
        
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
    require_roles,
)


# ═══════════════ Password hashing ═══════════════


class TestHashPassword:

    def test_returns_string(self):
        assert isinstance(hash_password("pw"), str)

    def test_not_plaintext(self):
        assert hash_password("secret") != "secret"

    def test_bcrypt_prefix(self):
        h = hash_password("x")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_unique_salt_each_call(self):
        assert hash_password("same") != hash_password("same")


class TestVerifyPassword:

    def test_correct_password(self):
        h = hash_password("right")
        assert verify_password("right", h) is True

    def test_wrong_password(self):
        h = hash_password("right")
        assert verify_password("wrong", h) is False

    def test_empty_password_matches_itself(self):
        h = hash_password("")
        assert verify_password("", h) is True

    def test_empty_password_rejects_nonempty(self):
        h = hash_password("")
        assert verify_password("notempty", h) is False


# ═══════════════ JWT creation ═══════════════


class TestCreateAccessToken:

    def test_returns_three_part_jwt(self):
        token = create_access_token({"sub": "u", "role": "user"})
        assert len(token.split(".")) == 3

    def test_claims_roundtrip(self):
        data = {"sub": "alice", "user_id": 7, "role": "admin"}
        payload = decode_token(create_access_token(data))
        assert payload["sub"] == "alice"
        assert payload["user_id"] == 7
        assert payload["role"] == "admin"

    def test_expiry_claim_present(self):
        payload = decode_token(create_access_token({"sub": "u", "role": "r"}))
        assert "exp" in payload

    def test_does_not_mutate_input_dict(self):
        d = {"sub": "u", "role": "r"}
        copy = d.copy()
        create_access_token(d)
        assert d == copy


# ═══════════════ JWT decoding ═══════════════


class TestDecodeToken:

    def test_valid_token(self):
        token = create_access_token({"sub": "bob", "user_id": 3, "role": "user"})
        p = decode_token(token)
        assert p["sub"] == "bob"

    def test_garbage_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not.a.jwt")
        assert exc.value.status_code == 401

    def test_empty_string_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("")
        assert exc.value.status_code == 401

    def test_tampered_signature_raises_401(self):
        token = create_access_token({"sub": "u", "role": "r"})
        bad = token[:-4] + "ZZZZ"
        with pytest.raises(HTTPException) as exc:
            decode_token(bad)
        assert exc.value.status_code == 401


# ═══════════════ get_current_user ═══════════════


class TestGetCurrentUser:

    def _creds(self, token: str):
        m = MagicMock()
        m.credentials = token
        return m

    def test_returns_user_dict(self):
        token = create_access_token({"sub": "carol", "user_id": 5, "role": "admin"})
        user = get_current_user(self._creds(token))
        assert user == {"id": 5, "username": "carol", "role": "admin"}

    def test_missing_sub_raises_401(self):
        token = create_access_token({"user_id": 1, "role": "user"})
        with pytest.raises(HTTPException) as exc:
            get_current_user(self._creds(token))
        assert exc.value.status_code == 401

    def test_missing_role_raises_401(self):
        token = create_access_token({"sub": "x", "user_id": 1})
        with pytest.raises(HTTPException) as exc:
            get_current_user(self._creds(token))
        assert exc.value.status_code == 401

    def test_invalid_jwt_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            get_current_user(self._creds("garbage"))
        assert exc.value.status_code == 401


# ═══════════════ require_roles ═══════════════


class TestRequireRoles:

    def test_allowed_single_role(self):
        fn = require_roles("admin")
        user = {"id": 1, "username": "a", "role": "admin"}
        assert fn(user) == user

    def test_allowed_multiple_roles(self):
        fn = require_roles("admin", "user")
        user = {"id": 2, "username": "b", "role": "user"}
        assert fn(user) == user

    def test_denied_raises_403(self):
        fn = require_roles("admin")
        user = {"id": 3, "username": "c", "role": "user"}
        with pytest.raises(HTTPException) as exc:
            fn(user)
        assert exc.value.status_code == 403
        assert "Insufficient permissions" in exc.value.detail

if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))