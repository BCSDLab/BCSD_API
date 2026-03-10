import random
import string
import time
from dataclasses import dataclass

import aiosmtplib
from email.message import EmailMessage


_CODE_TTL = 300
_CODE_LENGTH = 6


@dataclass
class _Pending:
    code: str
    expires: float


_store: dict[str, _Pending] = {}


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=_CODE_LENGTH))


def _build_message(sender: str, recipient: str, code: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "[BCSDLab] Email Verification Code"
    msg.set_content(f"Your verification code is: {code}\nExpires in 5 minutes.")
    return msg


async def send_code(email: str, host: str, port: int, user: str, password: str) -> None:
    code = _generate_code()
    _store[email] = _Pending(code=code, expires=time.time() + _CODE_TTL)
    msg = _build_message(user, email, code)
    await aiosmtplib.send(
        msg, hostname=host, port=port,
        username=user, password=password,
        use_tls=False, start_tls=True,
    )


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
