import logging

from bcsd_api.common.constants import ORG_ID
from bcsd_api.global_.exception import Forbidden

logger = logging.getLogger(__name__)


def require_permission(authz, permission: str, user_id: str) -> None:
    if not authz:
        return
    try:
        granted = authz.check("organization", ORG_ID, permission, user_id)
    except Exception:
        logger.warning("SpiceDB check failed, skipping authz")
        return
    if granted:
        return
    raise Forbidden(f"{permission} permission required")


def require_admin(authz, user_id: str) -> None:
    require_permission(authz, "admin", user_id)


def require_fee_edit(authz, user_id: str) -> None:
    require_permission(authz, "fee_edit", user_id)


def require_member_view(authz, user_id: str) -> None:
    require_permission(authz, "member_view", user_id)
