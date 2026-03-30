from strawberry.types import Info

from bcsd_api.authz.check import require_admin
from bcsd_api.graphql.context import GqlContext, require_user

from . import service


def resolve_setting(info: Info[GqlContext, None], key: str) -> str | None:
    require_user(info.context)
    return service.get_setting(info.context.setting_repo, key)


def resolve_set_setting(info: Info[GqlContext, None], key: str, value: str) -> bool:
    user = require_user(info.context)
    require_admin(info.context.authz, user["sub"])
    service.set_setting(info.context.setting_repo, key, value, user["sub"])
    return True
