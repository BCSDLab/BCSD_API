import strawberry
from pydantic import BaseModel

from bcsd_api.filter.base import SortField


@strawberry.input
class SortFieldInput:
    field: str
    order: str = "asc"


def to_sorts(inputs: list[SortFieldInput] | None) -> list[SortField]:
    if not inputs:
        return [SortField(field="id")]
    return [SortField(field=s.field, order=s.order) for s in inputs]


def from_model(source: BaseModel, target_cls):
    return target_cls(**source.model_dump())


def from_paged(paged, item_cls, paged_cls):
    items = [from_model(m, item_cls) for m in paged.items]
    return paged_cls(
        items=items, total=paged.total,
        page=paged.page, size=paged.size,
    )
