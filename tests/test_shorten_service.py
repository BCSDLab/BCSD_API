import re


def test_generate_code_format():
    from bcsd_api.shorten.service import _generate_code
    code = _generate_code()
    assert len(code) == 6
    assert re.match(r"^[a-z0-9]{6}$", code)


def test_create_link_random_code(mocker):
    from bcsd_api.shorten.service import create
    from bcsd_api.shorten.schema import CreateRequest

    repo = mocker.MagicMock()
    repo.find_by_code.return_value = None
    req = CreateRequest(title="test", url="https://example.com")
    result = create(repo, req, "M-123")
    repo.create.assert_called_once()
    row = repo.create.call_args[0][0]
    assert row["url"] == "https://example.com"
    assert row["title"] == "test"
    assert row["creator_id"] == "M-123"
    assert len(row["code"]) == 6


def test_create_link_custom_code(mocker):
    from bcsd_api.shorten.service import create
    from bcsd_api.shorten.schema import CreateRequest

    repo = mocker.MagicMock()
    repo.find_by_code.return_value = None
    req = CreateRequest(title="test", url="https://example.com", code="my-link")
    result = create(repo, req, "M-123")
    row = repo.create.call_args[0][0]
    assert row["code"] == "my-link"


def test_create_link_custom_code_conflict(mocker):
    import pytest
    from bcsd_api.shorten.service import create
    from bcsd_api.shorten.schema import CreateRequest
    from bcsd_api.exception import Conflict

    repo = mocker.MagicMock()
    repo.find_by_code.return_value = {"id": "existing"}
    req = CreateRequest(title="test", url="https://example.com", code="taken")
    with pytest.raises(Conflict):
        create(repo, req, "M-123")


def test_list_links(mocker):
    from bcsd_api.shorten.service import list_links
    from bcsd_api.filter.links import LinkFilter

    repo = mocker.MagicMock()
    repo.find_all.return_value = [
        {"id": "L-1", "code": "abc", "title": "t", "description": "",
         "url": "https://a.com", "creator_id": "M-1",
         "created_at": "2026-01-01", "expires_at": "",
         "expired_at": "", "updated_at": "2026-01-01"},
    ]
    filt = LinkFilter()
    result = list_links(repo, filt)
    assert result.total == 1


def test_get_detail_with_clicks(mocker):
    from bcsd_api.shorten.service import get_detail

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = {
        "id": "L-1", "code": "abc", "title": "t", "description": "",
        "url": "https://a.com", "creator_id": "M-1",
        "created_at": "2026-01-01", "expires_at": "",
        "expired_at": "", "updated_at": "2026-01-01",
    }
    repo.find_clicks.return_value = [
        {"clicked_at": "2026-01-01T10:00:00"},
        {"clicked_at": "2026-01-01T14:00:00"},
        {"clicked_at": "2026-01-02T09:00:00"},
    ]
    result = get_detail(repo, "L-1")
    assert result.total_clicks == 3
    assert len(result.daily_clicks) == 2


def test_get_detail_not_found(mocker):
    import pytest
    from bcsd_api.shorten.service import get_detail
    from bcsd_api.exception import NotFound

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = None
    with pytest.raises(NotFound):
        get_detail(repo, "L-999")


def test_update_link(mocker):
    from bcsd_api.shorten.service import update
    from bcsd_api.shorten.schema import UpdateRequest

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = {
        "id": "L-1", "creator_id": "M-1",
        "code": "abc", "title": "old", "description": "",
        "url": "https://a.com", "created_at": "2026-01-01",
        "expires_at": "", "expired_at": "", "updated_at": "2026-01-01",
    }
    req = UpdateRequest(title="new title")
    update(repo, "L-1", req)
    repo.update.assert_any_call("L-1", "title", "new title")


def test_toggle_expire(mocker):
    from bcsd_api.shorten.service import toggle

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = {
        "id": "L-1", "expired_at": "",
        "code": "abc", "title": "t", "description": "",
        "url": "https://a.com", "creator_id": "M-1",
        "created_at": "2026-01-01", "expires_at": "",
        "updated_at": "2026-01-01",
    }
    toggle(repo, "L-1")
    repo.update.assert_any_call("L-1", "expired_at", mocker.ANY)


def test_toggle_reopen(mocker):
    from bcsd_api.shorten.service import toggle

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = {
        "id": "L-1", "expired_at": "2026-01-01T00:00:00",
        "code": "abc", "title": "t", "description": "",
        "url": "https://a.com", "creator_id": "M-1",
        "created_at": "2026-01-01", "expires_at": "",
        "updated_at": "2026-01-01",
    }
    toggle(repo, "L-1")
    repo.update.assert_any_call("L-1", "expired_at", "")


def test_delete_link(mocker):
    from bcsd_api.shorten.service import delete

    repo = mocker.MagicMock()
    repo.find_by_id.return_value = {"id": "L-1", "creator_id": "M-1"}
    delete(repo, "L-1")
    repo.delete_clicks.assert_called_once_with("L-1")
    repo.delete.assert_called_once_with("L-1")


def test_resolve_expired_link(mocker):
    import pytest
    from bcsd_api.shorten.service import resolve
    from bcsd_api.exception import Gone

    repo = mocker.MagicMock()
    repo.find_by_code.return_value = {
        "id": "L-1", "url": "https://a.com",
        "expired_at": "2026-01-01T00:00:00", "expires_at": "",
    }
    with pytest.raises(Gone):
        resolve(repo, "abc")


def test_resolve_active_link(mocker):
    from bcsd_api.shorten.service import resolve

    repo = mocker.MagicMock()
    repo.find_by_code.return_value = {
        "id": "L-1", "url": "https://a.com",
        "expired_at": "", "expires_at": "",
    }
    url, link_id = resolve(repo, "abc")
    assert url == "https://a.com"
    assert link_id == "L-1"


def test_get_filters(mocker):
    from bcsd_api.shorten.service import get_filters

    repo = mocker.MagicMock()
    repo.find_all.return_value = [
        {"creator_id": "M-1"},
        {"creator_id": "M-1"},
        {"creator_id": "M-2"},
    ]
    members_repo = mocker.MagicMock()
    members_repo.find_by_id.side_effect = lambda mid: {"name": f"User {mid[-1]}"}
    result = get_filters(repo, members_repo)
    assert len(result.creators) == 2
