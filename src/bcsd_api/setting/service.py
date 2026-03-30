from .pg_repository import PgSettingRepository


def get_setting(repo: PgSettingRepository, key: str) -> str | None:
    return repo.get(key)


def set_setting(repo: PgSettingRepository, key: str, value: str, admin_id: str) -> None:
    repo.upsert(key, value, admin_id)
