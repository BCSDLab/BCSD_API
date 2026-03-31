import strawberry


@strawberry.type
class RecruitmentPeriodType:
    id: str
    type: str
    start_date: str
    end_date: str
    is_active: bool


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
    is_active: bool | None = None
