import pytest
from pydantic import ValidationError


def test_create_request_random_code():
    from bcsd_api.shorten.schema import CreateRequest
    req = CreateRequest(title="test", url="https://example.com")
    assert req.code is None
    assert req.expires_at is None


def test_create_request_custom_code():
    from bcsd_api.shorten.schema import CreateRequest
    req = CreateRequest(title="test", url="https://example.com", code="2025모집")
    assert req.code == "2025모집"


def test_create_request_code_too_short():
    from bcsd_api.shorten.schema import CreateRequest
    with pytest.raises(ValidationError):
        CreateRequest(title="test", url="https://example.com", code="a")


def test_create_request_code_too_long():
    from bcsd_api.shorten.schema import CreateRequest
    with pytest.raises(ValidationError):
        CreateRequest(title="test", url="https://example.com", code="a" * 101)


def test_create_request_code_reserved_chars():
    from bcsd_api.shorten.schema import CreateRequest
    with pytest.raises(ValidationError):
        CreateRequest(title="test", url="https://example.com", code="a/b")


def test_update_request():
    from bcsd_api.shorten.schema import UpdateRequest
    req = UpdateRequest(title="new title")
    assert req.description is None
    assert req.expires_at is None
