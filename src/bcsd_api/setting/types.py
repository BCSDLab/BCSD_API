import strawberry


@strawberry.type
class SettingType:
    key: str
    value: str
