from pydantic import BaseModel


def from_model(source: BaseModel, target_cls):
    return target_cls(**source.model_dump())


def from_paged(paged, item_cls, paged_cls):
    items = [from_model(m, item_cls) for m in paged.items]
    return paged_cls(
        items=items, total=paged.total,
        page=paged.page, size=paged.size,
    )
