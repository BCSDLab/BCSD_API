from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SortField(BaseModel):
    field: str
    order: str = "asc"


class BaseFilter(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sorts: list[SortField] = Field(default=[SortField(field="id")])

    search_fields: list[str] = Field(default=[], exclude=True)

    def filters(self) -> dict:
        excluded = {"page", "size", "sorts", "search_fields"}
        pairs = self.model_dump(exclude=excluded, exclude_none=True)
        return pairs


class PagedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


def _matches_row(row: dict, key: str, value: str, search: set[str]) -> bool:
    cell = row.get(key, "")
    if key in search:
        return value.lower() in cell.lower()
    return cell == value


def _row_matches(row: dict, criteria: dict, search: set[str]) -> bool:
    return all(_matches_row(row, k, v, search) for k, v in criteria.items())


def _filter_rows(rows: list[dict], filt: BaseFilter) -> list[dict]:
    criteria = filt.filters()
    if not criteria:
        return rows
    search = set(filt.search_fields)
    return [row for row in rows if _row_matches(row, criteria, search)]


def _valid_columns(rows: list[dict]) -> set[str]:
    if not rows:
        return set()
    return set(rows[0].keys())


def _sort_rows(rows: list[dict], filt: BaseFilter) -> list[dict]:
    valid = _valid_columns(rows)
    safe = [s for s in filt.sorts if s.field in valid]
    if not safe:
        return rows
    for s in reversed(safe):
        reverse = s.order == "desc"
        rows = sorted(rows, key=lambda r, f=s.field: r.get(f, ""), reverse=reverse)
    return rows


def apply_filter(rows: list[dict], filt: BaseFilter) -> PagedResponse:
    filtered = _filter_rows(rows, filt)
    sorted_rows = _sort_rows(filtered, filt)
    total = len(sorted_rows)
    start = (filt.page - 1) * filt.size
    page_rows = sorted_rows[start : start + filt.size]
    return PagedResponse(
        items=page_rows,
        total=total,
        page=filt.page,
        size=filt.size,
    )
