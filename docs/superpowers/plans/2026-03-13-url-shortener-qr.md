# URL 단축 + QR 코드 생성 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** URL 단축 (CRUD + 리다이렉트 + 통계) + QR 코드 생성 + SpiceDB 권한 모델 구현

**Architecture:** Google Sheets 기반 `links`/`link_clicks` 시트에 데이터 저장. `shorten/` 패키지가 CRUD + 필터 + 통계, `qr/` 패키지가 QR 생성, `redirect.py`가 공개 리다이렉트 처리. 권한은 SpiceDB로 레벨 기반 체크.

**Tech Stack:** FastAPI, gspread, qrcode[pil], SpiceDB (authzed), Pydantic

**Spec:** `docs/superpowers/specs/2026-03-13-url-shortener-qr-design.md`

---

## File Structure

### 신규 생성

| 파일 | 역할 |
|------|------|
| `src/bcsd_api/shorten/__init__.py` | 패키지 init |
| `src/bcsd_api/shorten/router.py` | 8개 엔드포인트 |
| `src/bcsd_api/shorten/service.py` | 생성/목록/상세/수정/토글/삭제/필터 로직 |
| `src/bcsd_api/shorten/schema.py` | Request/Response Pydantic 모델 |
| `src/bcsd_api/shorten/repository.py` | links + link_clicks 시트 접근 |
| `src/bcsd_api/qr/__init__.py` | 패키지 init |
| `src/bcsd_api/qr/router.py` | GET /v1/qr |
| `src/bcsd_api/qr/schema.py` | QrParams 모델 |
| `src/bcsd_api/qr/service.py` | QR 생성 로직 |
| `src/bcsd_api/redirect.py` | GET /s/{code} 리다이렉트 |
| `src/bcsd_api/filter/links.py` | LinkFilter 클래스 |
| `src/bcsd_api/sheets/migrations/V003_links_and_roles.py` | 마이그레이션 |
| `tests/test_shorten_service.py` | shorten 서비스 테스트 |
| `tests/test_qr_service.py` | QR 서비스 테스트 |
| `tests/test_shorten_schema.py` | 스키마 검증 테스트 |

### 수정

| 파일 | 변경 |
|------|------|
| `src/bcsd_api/sheets/client.py` | `delete_row`, `delete_rows` 추가 |
| `src/bcsd_api/exception/errors.py` | `Gone` (410) 추가 |
| `src/bcsd_api/main.py` | 3개 라우터 등록 |
| `src/bcsd_api/dependencies.py` | `get_link_repo` 추가 |
| `pyproject.toml` | `qrcode[pil]` 의존성 추가 |
| `infra/nginx/bcsd-api.conf.template` | `/s/` location 추가 |

---

## Chunk 1: 사전 작업 (기존 코드 수정)

### Task 1: SheetsClient에 delete 메서드 추가

**Files:**
- Modify: `src/bcsd_api/sheets/client.py:40-61`
- Test: `tests/test_sheets_delete.py`

- [ ] **Step 1: Write failing tests for delete_row and delete_rows**

```python
# tests/test_sheets_delete.py
from bcsd_api.sheets.client import SheetsClient


def test_delete_row_removes_matching_row(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [
        {"id": "1", "name": "a"},
        {"id": "2", "name": "b"},
    ]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_row("sheet", "id", "1")
    mock_ws.delete_rows.assert_called_once_with(2)


def test_delete_row_no_match(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [{"id": "1"}]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_row("sheet", "id", "99")
    mock_ws.delete_rows.assert_not_called()


def test_delete_rows_removes_all_matching(mocker):
    mock_ws = mocker.MagicMock()
    mock_ws.get_all_records.return_value = [
        {"id": "1", "link_id": "L1"},
        {"id": "2", "link_id": "L1"},
        {"id": "3", "link_id": "L2"},
    ]
    client = SheetsClient.__new__(SheetsClient)
    client._spreadsheet = mocker.MagicMock()
    client._spreadsheet.worksheet.return_value = mock_ws
    client.delete_rows("sheet", "link_id", "L1")
    # 역순 삭제: row 3 (idx 1) 먼저, row 2 (idx 0) 나중
    assert mock_ws.delete_rows.call_count == 2
    mock_ws.delete_rows.assert_any_call(3)
    mock_ws.delete_rows.assert_any_call(2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sheets_delete.py -v`
Expected: FAIL — `SheetsClient` has no `delete_row`/`delete_rows`

- [ ] **Step 3: Implement delete_row and delete_rows**

Add to `src/bcsd_api/sheets/client.py` after `update_cell`:

```python
def delete_row(self, sheet_name: str, column: str, value: str) -> None:
    worksheet = self._spreadsheet.worksheet(sheet_name)
    records = worksheet.get_all_records()
    idx = self._find_index(records, column, value)
    if idx is None:
        return
    worksheet.delete_rows(idx + 2)

def delete_rows(self, sheet_name: str, column: str, value: str) -> None:
    worksheet = self._spreadsheet.worksheet(sheet_name)
    records = worksheet.get_all_records()
    indices = []
    for i, record in enumerate(records):
        if self._matches(record, column, value):
            indices.append(i + 2)
    for row_num in reversed(indices):
        worksheet.delete_rows(row_num)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sheets_delete.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/sheets/client.py tests/test_sheets_delete.py
git commit -m "feat(sheets): add delete_row and delete_rows to SheetsClient"
```

---

### Task 2: Gone 예외 클래스 추가

**Files:**
- Modify: `src/bcsd_api/exception/errors.py`

- [ ] **Step 1: Add Gone exception**

Append to `src/bcsd_api/exception/errors.py`:

```python
class Gone(AppException):
    status_code = 410
    error_code = "GONE"
    message = "resource is no longer available"
```

- [ ] **Step 2: Export Gone from exception __init__**

Update `src/bcsd_api/exception/__init__.py`:

```python
from .base import AppException
from .errors import BadRequest, Conflict, Forbidden, Gone, NotFound, Unauthorized
from .handlers import register_handlers

__all__ = [
    "AppException",
    "BadRequest",
    "Conflict",
    "Forbidden",
    "Gone",
    "NotFound",
    "Unauthorized",
    "register_handlers",
]
```

- [ ] **Step 3: Commit**

```bash
git add src/bcsd_api/exception/errors.py src/bcsd_api/exception/__init__.py
git commit -m "feat(exception): add Gone (410) exception class"
```

---

### Task 3: 의존성 추가 + 마이그레이션 V003

**Files:**
- Modify: `pyproject.toml:9-20`
- Create: `src/bcsd_api/sheets/migrations/V003_links_and_roles.py`

- [ ] **Step 1: Add qrcode[pil] and pytest-mock to pyproject.toml**

Add `"qrcode[pil]>=8.0",` to `dependencies` and `"pytest-mock>=3.0",` to `[project.optional-dependencies] dev` in `pyproject.toml`.

- [ ] **Step 2: Install dependencies**

Run: `pip install -e ".[dev]"`

- [ ] **Step 3: Write V003 migration**

```python
# src/bcsd_api/sheets/migrations/V003_links_and_roles.py
import gspread

from .helpers import add_column, add_sheets


_SCHEMAS: dict[str, list[str]] = {
    "links": [
        "id", "code", "title", "description", "url",
        "creator_id", "created_at", "expires_at",
        "expired_at", "updated_at",
    ],
    "link_clicks": [
        "id", "link_id", "clicked_at", "referer", "user_agent",
    ],
}


def upgrade(spreadsheet: gspread.Spreadsheet) -> None:
    add_sheets(spreadsheet, _SCHEMAS)
    add_column(spreadsheet, "members", "team", "role")
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml src/bcsd_api/sheets/migrations/V003_links_and_roles.py
git commit -m "feat(infra): add qrcode dep and V003 migration for links/roles"
```

---

## Chunk 2: QR 코드 모듈 (독립, 의존성 없음)

### Task 4: QR 스키마

**Files:**
- Create: `src/bcsd_api/qr/__init__.py`
- Create: `src/bcsd_api/qr/schema.py`
- Test: `tests/test_qr_schema.py`

- [ ] **Step 1: Write failing test for QrParams validation**

```python
# tests/test_qr_schema.py
import pytest
from pydantic import ValidationError


def test_qr_params_defaults():
    from bcsd_api.qr.schema import QrParams
    params = QrParams(text="hello")
    assert params.format == "png"
    assert params.size == 300


def test_qr_params_svg():
    from bcsd_api.qr.schema import QrParams
    params = QrParams(text="hello", format="svg", size=500)
    assert params.format == "svg"
    assert params.size == 500


def test_qr_params_invalid_format():
    from bcsd_api.qr.schema import QrParams
    with pytest.raises(ValidationError):
        QrParams(text="hello", format="gif")


def test_qr_params_size_too_small():
    from bcsd_api.qr.schema import QrParams
    with pytest.raises(ValidationError):
        QrParams(text="hello", size=50)


def test_qr_params_size_too_large():
    from bcsd_api.qr.schema import QrParams
    with pytest.raises(ValidationError):
        QrParams(text="hello", size=1500)


def test_qr_params_text_too_long():
    from bcsd_api.qr.schema import QrParams
    with pytest.raises(ValidationError):
        QrParams(text="a" * 2001)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_qr_schema.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement QrParams**

```python
# src/bcsd_api/qr/__init__.py
```

```python
# src/bcsd_api/qr/schema.py
from pydantic import BaseModel, Field


class QrParams(BaseModel):
    text: str = Field(..., max_length=2000)
    format: str = Field("png", pattern="^(png|svg)$")
    size: int = Field(300, ge=100, le=1000)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_qr_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/qr/ tests/test_qr_schema.py
git commit -m "feat(qr): add QrParams schema with validation"
```

---

### Task 5: QR 서비스 (PNG + SVG 생성)

**Files:**
- Create: `src/bcsd_api/qr/service.py`
- Test: `tests/test_qr_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_qr_service.py


def test_generate_png():
    from bcsd_api.qr.service import generate
    data = generate("hello", "png", 300)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_svg():
    from bcsd_api.qr.service import generate
    data = generate("hello", "svg", 300)
    assert b"<svg" in data


def test_generate_korean():
    from bcsd_api.qr.service import generate
    data = generate("한글 테스트", "png", 300)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_qr_service.py -v`
Expected: FAIL

- [ ] **Step 3: Implement QR generation**

```python
# src/bcsd_api/qr/service.py
from io import BytesIO

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.svg import SvgPathImage


def generate(text: str, fmt: str, size: int) -> bytes:
    if fmt == "svg":
        return _generate_svg(text)
    return _generate_png(text, size)


def _generate_png(text: str, size: int) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(image_factory=StyledPilImage)
    img = img.resize((size, size))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_svg(text: str) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(image_factory=SvgPathImage)
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_qr_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/qr/service.py tests/test_qr_service.py
git commit -m "feat(qr): implement PNG and SVG QR code generation"
```

---

### Task 6: QR 라우터

**Files:**
- Create: `src/bcsd_api/qr/router.py`

- [ ] **Step 1: Implement QR router**

```python
# src/bcsd_api/qr/router.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO

from bcsd_api.dependencies import current_user

from . import service
from .schema import QrParams

router = APIRouter(prefix="/v1/qr", tags=["qr"])


_MEDIA_TYPES = {"png": "image/png", "svg": "image/svg+xml"}


@router.get("")
def generate_qr(
    params: QrParams = Depends(),
    _: dict = Depends(current_user),
) -> StreamingResponse:
    data = service.generate(params.text, params.format, params.size)
    media = _MEDIA_TYPES[params.format]
    return StreamingResponse(BytesIO(data), media_type=media)
```

- [ ] **Step 2: Commit**

```bash
git add src/bcsd_api/qr/router.py
git commit -m "feat(qr): add GET /v1/qr router"
```

---

## Chunk 3: Shorten 모듈 (스키마 + 레포지토리 + 필터)

### Task 7: Shorten 스키마

**Files:**
- Create: `src/bcsd_api/shorten/__init__.py`
- Create: `src/bcsd_api/shorten/schema.py`
- Test: `tests/test_shorten_schema.py`

- [ ] **Step 1: Write failing tests for schema validation**

```python
# tests/test_shorten_schema.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_shorten_schema.py -v`
Expected: FAIL

- [ ] **Step 3: Implement schemas**

```python
# src/bcsd_api/shorten/__init__.py
```

```python
# src/bcsd_api/shorten/schema.py
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_RESERVED = re.compile(r"[/\?#&=%\\]")


class CreateRequest(BaseModel):
    title: str
    description: str | None = None
    url: str
    code: str | None = None
    expires_at: datetime | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v is None:
            return v
        if len(v) < 2 or len(v) > 100:
            raise ValueError("code must be 2-100 characters")
        if _RESERVED.search(v):
            raise ValueError("code contains reserved characters")
        return v


class UpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    expires_at: datetime | None = None


class LinkResponse(BaseModel):
    id: str
    code: str
    title: str
    description: str | None = None
    url: str
    creator_id: str
    created_at: str
    expires_at: str | None = None
    expired_at: str | None = None
    updated_at: str

    @field_validator("expires_at", "expired_at", "description", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v


class DailyClick(BaseModel):
    date: str
    count: int


class LinkDetail(LinkResponse):
    total_clicks: int
    daily_clicks: list[DailyClick]


class CreatorOption(BaseModel):
    id: str
    name: str


class LinkFiltersResponse(BaseModel):
    creators: list[CreatorOption]
    expired: list[str] = ["active", "expired", "all"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_shorten_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/shorten/ tests/test_shorten_schema.py
git commit -m "feat(shorten): add request/response schemas"
```

---

### Task 8: LinkFilter

**Files:**
- Create: `src/bcsd_api/filter/links.py`

- [ ] **Step 1: Implement LinkFilter**

```python
# src/bcsd_api/filter/links.py
from pydantic import field_validator

from .base import BaseFilter


class LinkFilter(BaseFilter):
    creator_id: str | None = None
    expired: str | None = None

    @field_validator("expired", mode="before")
    @classmethod
    def all_to_none(cls, v):
        if v == "all":
            return None
        return v
```

Note: `expired="all"`은 `None`으로 변환되어 `filters()`에서 `exclude_none=True`로 스킵됨. `expired` 필터는 서비스 레이어에서 전처리 후 `BaseFilter`의 문자열 비교로 처리. `expired` 값은 서비스에서 각 row에 computed 컬럼으로 추가.

- [ ] **Step 2: Commit**

```bash
git add src/bcsd_api/filter/links.py
git commit -m "feat(filter): add LinkFilter class"
```

---

### Task 9: Shorten 레포지토리

**Files:**
- Create: `src/bcsd_api/shorten/repository.py`
- Modify: `src/bcsd_api/dependencies.py`

- [ ] **Step 1: Implement repository**

```python
# src/bcsd_api/shorten/repository.py
from bcsd_api.sheets.client import SheetsClient

_LINKS = "links"
_CLICKS = "link_clicks"


class LinkRepository:
    def __init__(self, sheets: SheetsClient):
        self._sheets = sheets

    def find_all(self) -> list[dict]:
        return self._sheets.get_records(_LINKS)

    def find_by_id(self, link_id: str) -> dict | None:
        return self._sheets.find_row(_LINKS, "id", link_id)

    def find_by_code(self, code: str) -> dict | None:
        return self._sheets.find_row(_LINKS, "code", code)

    def create(self, row: dict) -> None:
        self._sheets.append_row(_LINKS, row)

    def update(self, link_id: str, column: str, value: str) -> None:
        self._sheets.update_cell(_LINKS, "id", link_id, column, value)

    def delete(self, link_id: str) -> None:
        self._sheets.delete_row(_LINKS, "id", link_id)

    def find_clicks(self, link_id: str) -> list[dict]:
        records = self._sheets.get_records(_CLICKS)
        return [r for r in records if r.get("link_id") == link_id]

    def add_click(self, row: dict) -> None:
        self._sheets.append_row(_CLICKS, row)

    def delete_clicks(self, link_id: str) -> None:
        self._sheets.delete_rows(_CLICKS, "link_id", link_id)
```

- [ ] **Step 2: Add get_link_repo to dependencies.py**

Add to `src/bcsd_api/dependencies.py`:

```python
from .shorten.repository import LinkRepository

def get_link_repo(sheets: SheetsClient = Depends(get_sheets)) -> LinkRepository:
    return LinkRepository(sheets)
```

- [ ] **Step 3: Commit**

```bash
git add src/bcsd_api/shorten/repository.py src/bcsd_api/dependencies.py
git commit -m "feat(shorten): add LinkRepository and dependency"
```

---

## Chunk 4: Shorten 서비스

### Task 10: Shorten 서비스 — 코드 생성 + 생성

**Files:**
- Create: `src/bcsd_api/shorten/service.py`
- Test: `tests/test_shorten_service.py`

- [ ] **Step 1: Write failing tests for code generation and create**

```python
# tests/test_shorten_service.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_shorten_service.py -v`
Expected: FAIL

- [ ] **Step 3: Implement service (create + code generation)**

```python
# src/bcsd_api/shorten/service.py
import random
import string
from collections import Counter
from datetime import datetime

from bcsd_api.exception import Conflict, Gone, NotFound
from bcsd_api.filter.base import PagedResponse, apply_filter
from bcsd_api.filter.links import LinkFilter
from bcsd_api.id_gen import generate_id
from bcsd_api.member.repository import MemberRepository
from bcsd_api.timezone import KST

from .repository import LinkRepository
from .schema import (
    CreateRequest,
    CreatorOption,
    DailyClick,
    LinkDetail,
    LinkFiltersResponse,
    LinkResponse,
    UpdateRequest,
)

_MAX_RETRIES = 5


def _generate_code() -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=6))


def _now_str() -> str:
    return datetime.now(KST).isoformat()


def _format_expires(expires_at) -> str:
    if not expires_at:
        return ""
    return expires_at.isoformat()


def _resolve_code(repo: LinkRepository, code: str | None) -> str:
    if not code:
        return _unique_code(repo)
    if repo.find_by_code(code):
        raise Conflict(f"code '{code}' already exists")
    return code


def _build_row(code: str, req: CreateRequest, creator_id: str) -> dict:
    now = _now_str()
    return {
        "id": generate_id("L"),
        "code": code,
        "title": req.title,
        "description": req.description or "",
        "url": req.url,
        "creator_id": creator_id,
        "created_at": now,
        "expires_at": _format_expires(req.expires_at),
        "expired_at": "",
        "updated_at": now,
    }


def create(repo: LinkRepository, req: CreateRequest, creator_id: str) -> LinkResponse:
    code = _resolve_code(repo, req.code)
    row = _build_row(code, req, creator_id)
    repo.create(row)
    return LinkResponse(**row)


def _unique_code(repo: LinkRepository) -> str:
    for _ in range(_MAX_RETRIES):
        code = _generate_code()
        if not repo.find_by_code(code):
            return code
    raise Conflict("failed to generate unique code")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_shorten_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/shorten/service.py tests/test_shorten_service.py
git commit -m "feat(shorten): implement create link with code generation"
```

---

### Task 11: Shorten 서비스 — 목록 + 상세 + 통계

**Files:**
- Modify: `src/bcsd_api/shorten/service.py`
- Modify: `tests/test_shorten_service.py`

- [ ] **Step 1: Write failing tests for list and detail**

Append to `tests/test_shorten_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_shorten_service.py -v`
Expected: FAIL on new tests

- [ ] **Step 3: Implement list_links and get_detail**

Add to `src/bcsd_api/shorten/service.py`:

```python
def _is_expired(row: dict) -> bool:
    if row.get("expired_at"):
        return True
    expires = row.get("expires_at")
    if not expires:
        return False
    return datetime.fromisoformat(expires) < datetime.now(KST)


def _expired_label(row: dict) -> str:
    if _is_expired(row):
        return "expired"
    return "active"


def _add_expired_flag(rows: list[dict]) -> list[dict]:
    for row in rows:
        row["expired"] = _expired_label(row)
    return rows


def list_links(repo: LinkRepository, filt: LinkFilter) -> PagedResponse[LinkResponse]:
    rows = _add_expired_flag(repo.find_all())
    paged = apply_filter(rows, filt)
    items = [LinkResponse(**r) for r in paged.items]
    return PagedResponse(
        items=items, total=paged.total, page=paged.page, size=paged.size
    )


def _aggregate_clicks(clicks: list[dict]) -> list[DailyClick]:
    dates = []
    for c in clicks:
        raw = c.get("clicked_at", "")
        if not raw:
            continue
        dates.append(raw[:10])
    counts = Counter(dates)
    return [DailyClick(date=d, count=n) for d, n in sorted(counts.items())]


def get_detail(repo: LinkRepository, link_id: str) -> LinkDetail:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    clicks = repo.find_clicks(link_id)
    return LinkDetail(
        **row,
        total_clicks=len(clicks),
        daily_clicks=_aggregate_clicks(clicks),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_shorten_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/shorten/service.py tests/test_shorten_service.py
git commit -m "feat(shorten): implement list and detail with click stats"
```

---

### Task 12: Shorten 서비스 — 수정 + 토글 + 삭제 + 필터 + 리다이렉트

**Files:**
- Modify: `src/bcsd_api/shorten/service.py`
- Modify: `tests/test_shorten_service.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_shorten_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_shorten_service.py -v`
Expected: FAIL on new tests

- [ ] **Step 3: Implement remaining service functions**

Add to `src/bcsd_api/shorten/service.py`:

```python
def _serialize_field(key: str, val) -> str:
    if key == "expires_at" and val:
        return val.isoformat()
    if key == "expires_at":
        return ""
    return str(val)


def _apply_updates(repo: LinkRepository, link_id: str, updates: dict) -> None:
    for key, val in updates.items():
        repo.update(link_id, key, _serialize_field(key, val))
    repo.update(link_id, "updated_at", _now_str())


def update(repo: LinkRepository, link_id: str, req: UpdateRequest) -> LinkResponse:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    updates = req.model_dump(exclude_none=True)
    _apply_updates(repo, link_id, updates)
    return LinkResponse(**{**row, **updates, "updated_at": _now_str()})


def toggle(repo: LinkRepository, link_id: str) -> LinkResponse:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    if row.get("expired_at"):
        repo.update(link_id, "expired_at", "")
        row["expired_at"] = ""
        repo.update(link_id, "updated_at", _now_str())
        return LinkResponse(**row)
    now = _now_str()
    repo.update(link_id, "expired_at", now)
    row["expired_at"] = now
    repo.update(link_id, "updated_at", _now_str())
    return LinkResponse(**row)


def delete(repo: LinkRepository, link_id: str) -> None:
    row = repo.find_by_id(link_id)
    if not row:
        raise NotFound(f"link {link_id} not found")
    repo.delete_clicks(link_id)
    repo.delete(link_id)


def resolve(repo: LinkRepository, code: str) -> tuple[str, str]:
    row = repo.find_by_code(code)
    if not row:
        raise NotFound(f"short link '{code}' not found")
    if row.get("expired_at"):
        raise Gone("this link has expired")
    expires = row.get("expires_at")
    if expires and datetime.fromisoformat(expires) < datetime.now(KST):
        raise Gone("this link has expired")
    return row["url"], row["id"]


def record_click(repo: LinkRepository, link_id: str, referer: str, user_agent: str) -> None:
    row = {
        "id": generate_id("LC"),
        "link_id": link_id,
        "clicked_at": _now_str(),
        "referer": referer or "",
        "user_agent": user_agent or "",
    }
    repo.add_click(row)


def _creator_name(members_repo: MemberRepository, cid: str) -> str:
    member = members_repo.find_by_id(cid)
    if not member:
        return cid
    return member["name"]


def get_filters(repo: LinkRepository, members_repo: MemberRepository) -> LinkFiltersResponse:
    rows = repo.find_all()
    ids = list({r["creator_id"] for r in rows if r.get("creator_id")})
    creators = [CreatorOption(id=cid, name=_creator_name(members_repo, cid)) for cid in ids]
    return LinkFiltersResponse(creators=creators)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_shorten_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bcsd_api/shorten/service.py tests/test_shorten_service.py
git commit -m "feat(shorten): implement update, toggle, delete, resolve, filters"
```

---

## Chunk 5: 라우터 + 리다이렉트 + main.py 등록

### Task 13: Shorten 라우터

**Files:**
- Create: `src/bcsd_api/shorten/router.py`

- [ ] **Step 1: Implement shorten router**

```python
# src/bcsd_api/shorten/router.py
from fastapi import APIRouter, Depends

from bcsd_api.dependencies import current_user, get_link_repo, get_member_repo
from bcsd_api.filter.base import PagedResponse
from bcsd_api.filter.links import LinkFilter
from bcsd_api.member.repository import MemberRepository

from . import service
from .repository import LinkRepository
from .schema import (
    CreateRequest,
    LinkDetail,
    LinkFiltersResponse,
    LinkResponse,
    UpdateRequest,
)

router = APIRouter(prefix="/v1/shorten", tags=["shorten"])


@router.post("", response_model=LinkResponse, status_code=201)
def create_link(
    req: CreateRequest,
    user: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.create(repo, req, user["sub"])


@router.get("/filters", response_model=LinkFiltersResponse)
def get_filters(
    repo: LinkRepository = Depends(get_link_repo),
    members_repo: MemberRepository = Depends(get_member_repo),
    _: dict = Depends(current_user),
) -> LinkFiltersResponse:
    return service.get_filters(repo, members_repo)


@router.get("", response_model=PagedResponse[LinkResponse])
def list_links(
    filt: LinkFilter = Depends(),
    _: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> PagedResponse[LinkResponse]:
    return service.list_links(repo, filt)


@router.get("/{link_id}", response_model=LinkDetail)
def get_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> LinkDetail:
    return service.get_detail(repo, link_id)


@router.post("/{link_id}", response_model=LinkResponse)
def update_link(
    link_id: str,
    req: UpdateRequest,
    _: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.update(repo, link_id, req)


@router.patch("/{link_id}/toggle", response_model=LinkResponse)
def toggle_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> LinkResponse:
    return service.toggle(repo, link_id)


@router.delete("/{link_id}", status_code=204)
def delete_link(
    link_id: str,
    _: dict = Depends(current_user),
    repo: LinkRepository = Depends(get_link_repo),
) -> None:
    service.delete(repo, link_id)
```

Note: 권한 체크(SpiceDB)는 서비스 레이어에서 처리. 현 단계에서는 인증만 확인하고, SpiceDB 통합은 Task 15에서 추가.

- [ ] **Step 2: Commit**

```bash
git add src/bcsd_api/shorten/router.py
git commit -m "feat(shorten): add router with 8 endpoints"
```

---

### Task 14: 리다이렉트 라우터 + main.py 등록

**Files:**
- Create: `src/bcsd_api/redirect.py`
- Modify: `src/bcsd_api/main.py:9-13, 61-63`

- [ ] **Step 1: Implement redirect router**

```python
# src/bcsd_api/redirect.py
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import RedirectResponse

from bcsd_api.dependencies import get_link_repo
from bcsd_api.shorten import service
from bcsd_api.shorten.repository import LinkRepository

router = APIRouter(tags=["redirect"])


@router.get("/s/{code}")
def redirect_link(
    code: str,
    request: Request,
    background: BackgroundTasks,
    repo: LinkRepository = Depends(get_link_repo),
) -> RedirectResponse:
    url, link_id = service.resolve(repo, code)
    referer = request.headers.get("referer", "")
    agent = request.headers.get("user-agent", "")
    background.add_task(service.record_click, repo, link_id, referer, agent)
    return RedirectResponse(url=url, status_code=302)
```

- [ ] **Step 2: Register all routers in main.py**

Add imports and `include_router` calls to `src/bcsd_api/main.py`:

```python
# Add to imports:
from .shorten.router import router as shorten_router
from .qr.router import router as qr_router
from .redirect import router as redirect_router

# Add to create_app(), after track_router:
app.include_router(shorten_router)
app.include_router(qr_router)
app.include_router(redirect_router)
```

- [ ] **Step 3: Commit**

```bash
git add src/bcsd_api/redirect.py src/bcsd_api/main.py
git commit -m "feat: add redirect router and register all new routers"
```

---

### Task 15: nginx /s/ location 추가

**Files:**
- Modify: `infra/nginx/bcsd-api.conf.template:104-124`

- [ ] **Step 1: Add /s/ location to stage.bcsdlab.com server block**

In the `HTTPS: Frontend` server block, add `/s/` location **before** the existing `/v1/` location:

```nginx
    location /s/ {
        proxy_pass http://api_blue;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_read_timeout 60s;
    }
```

- [ ] **Step 2: Commit**

```bash
git add infra/nginx/bcsd-api.conf.template
git commit -m "feat(infra): add /s/ location for short URL redirect"
```

---

## Chunk 6: SpiceDB 권한 모델 (후순위)

### Task 16: SpiceDB 스키마 + 권한 체크 통합

**Files:**
- Modify: `spicedb/schema.zed` (또는 새로 생성)
- Modify: `src/bcsd_api/shorten/service.py` — update, toggle, delete에 권한 체크 추가
- Modify: `src/bcsd_api/shorten/router.py` — authz 의존성 주입

Note: SpiceDB 스키마 설계와 권한 레벨 매핑은 별도 설계가 필요할 수 있음. 현재 `AuthzClient`는 기본 CRUD(check, add_relation, remove_relation)만 지원. 레벨 기반 비교 로직(`max(status, role)`)을 SpiceDB 스키마로 표현하거나, 서비스 레이어에서 레벨 비교 후 체크하는 방식 중 선택 필요.

- [ ] **Step 1: 권한 레벨 유틸 작성**

```python
# src/bcsd_api/permission.py
_STATUS_LEVEL = {
    "General": 0, "Beginner": 1, "Regular": 2, "Mentor": 7,
}
_ROLE_LEVEL = {
    "edu_leader": 3, "track_leader": 4,
    "vice_president": 5, "president": 6,
}


def level(status: str, role: str | None) -> int:
    s = _STATUS_LEVEL.get(status, 0)
    r = _ROLE_LEVEL.get(role or "", 0)
    return max(s, r)
```

- [ ] **Step 2: 서비스에 권한 체크 추가**

update, toggle, delete 함수에서 현재 사용자의 레벨과 생성자의 레벨을 비교하여 권한 체크. 상세 구현은 SpiceDB 스키마 확정 후 진행.

- [ ] **Step 3: Commit**

```bash
git add src/bcsd_api/permission.py src/bcsd_api/shorten/service.py src/bcsd_api/shorten/router.py
git commit -m "feat(authz): add permission level check for shorten CRUD"
```

---

## 실행 순서 요약

1. **Chunk 1** (Task 1-3): 사전 작업 — SheetsClient 확장, Gone 예외, 의존성/마이그레이션
2. **Chunk 2** (Task 4-6): QR 모듈 — 독립적, 병렬 가능
3. **Chunk 3** (Task 7-9): Shorten 스키마 + 레포 + 필터
4. **Chunk 4** (Task 10-12): Shorten 서비스 로직
5. **Chunk 5** (Task 13-15): 라우터 + 리다이렉트 + nginx
6. **Chunk 6** (Task 16): SpiceDB 권한 통합
