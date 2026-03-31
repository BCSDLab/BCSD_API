import secrets
import time
from dataclasses import dataclass

from bcsd_api.infra.email.sender import EmailSender
from bcsd_api.infra.email.template import verify_body


_CODE_TTL = 600
_CODE_LENGTH = 6
_SUBJECT = "[BCSD] 이메일 인증"


@dataclass
class _Pending:
    code: str
    expires: float


_store: dict[str, _Pending] = {}


def _generate_code() -> str:
    upper = 10 ** _CODE_LENGTH
    return str(secrets.randbelow(upper)).zfill(_CODE_LENGTH)


def send_code(email: str, sender: EmailSender) -> None:
    code = _generate_code()
    _store[email] = _Pending(code=code, expires=time.time() + _CODE_TTL)
    sender.send(to=email, subject=_SUBJECT, body=verify_body(code))


def confirm_code(email: str, code: str) -> bool:
    pending = _store.get(email)
    if not pending:
        return False
    if time.time() > pending.expires:
        _store.pop(email, None)
        return False
    if pending.code != code:
        return False
    _store.pop(email, None)
    return True


def is_verified(email: str) -> bool:
    return email not in _store
