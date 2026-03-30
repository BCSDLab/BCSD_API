import strawberry


@strawberry.type
class PeriodType:
    id: str
    title: str
    type: str
    start_date: str
    end_date: str
    is_active: str
    created_by: str | None
    created_at: str | None
    updated_at: str | None


@strawberry.input
class CreatePeriodInput:
    title: str
    type: str
    start_date: str
    end_date: str


@strawberry.input
class UpdatePeriodInput:
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_active: str | None = None
