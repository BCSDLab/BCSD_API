from bcsd_api.exception import Forbidden

ORG_ID = "bcsdlab"


def require_permission(authz, permission: str, user_id: str) -> None:
    if not authz:
        return
    if authz.check("organization", ORG_ID, permission, user_id):
        return
    raise Forbidden(f"{permission} permission required")


def require_admin(authz, user_id: str) -> None:
    require_permission(authz, "admin", user_id)


def require_fee_edit(authz, user_id: str) -> None:
    require_permission(authz, "fee_edit", user_id)


def require_member_view(authz, user_id: str) -> None:
    require_permission(authz, "member_view", user_id)
