"""
Module 7 – app.utils.exception   (Priority 4 – Wrong error responses)

Tests cover:
  • AppException  (default & custom status codes)
  • NotFoundException  (defaults to 404)
  • UnauthorizedException  (defaults to 401)
  • InternalServerException  (defaults to 500)
  • Inheritance chain
"""

import os
import sys

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.exception import (
    AppException,
    NotFoundException,
    UnauthorizedException,
    InternalServerException,
)


# ═══════════════ AppException ═══════════════


class TestAppException:

    def test_default_status_400(self):
        e = AppException("bad request")
        assert e.message == "bad request"
        assert e.status_code == 400

    def test_custom_status(self):
        e = AppException("conflict", 409)
        assert e.status_code == 409

    def test_is_exception(self):
        assert isinstance(AppException("x"), Exception)

    def test_str_and_message_match(self):
        e = AppException("msg")
        assert e.message == "msg"


# ═══════════════ NotFoundException ═══════════════


class TestNotFoundException:

    def test_default_message(self):
        e = NotFoundException()
        assert e.message == "Resource not found"
        assert e.status_code == 404

    def test_custom_message(self):
        e = NotFoundException("Book not found")
        assert e.message == "Book not found"
        assert e.status_code == 404

    def test_inherits_app_exception(self):
        assert isinstance(NotFoundException(), AppException)

    def test_is_base_exception(self):
        assert isinstance(NotFoundException(), Exception)


# ═══════════════ UnauthorizedException ═══════════════


class TestUnauthorizedException:

    def test_default_message(self):
        e = UnauthorizedException()
        assert e.message == "Unauthorized"
        assert e.status_code == 401

    def test_custom_message(self):
        e = UnauthorizedException("Token expired")
        assert e.message == "Token expired"
        assert e.status_code == 401

    def test_inherits_app_exception(self):
        assert isinstance(UnauthorizedException(), AppException)


# ═══════════════ InternalServerException ═══════════════


class TestInternalServerException:

    def test_default_message(self):
        e = InternalServerException()
        assert e.message == "Internal server error"
        assert e.status_code == 500

    def test_custom_message(self):
        e = InternalServerException("DB crashed")
        assert e.message == "DB crashed"
        assert e.status_code == 500

    def test_inherits_app_exception(self):
        assert isinstance(InternalServerException(), AppException)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))