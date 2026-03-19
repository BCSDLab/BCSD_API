from datetime import datetime, timedelta, timezone

from fastapi import Request
from jose import JWTError, jwt

from bcsd_api.exception import Unauthorized


def create_token(payload: dict, secret: str, algorithm: str, minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    data = {**payload, "exp": expire}
    return jwt.encode(data, secret, algorithm=algorithm)


def decode_token(token: str, secret: str, algorithm: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError:
        raise Unauthorized("invalid or expired token")


def extract_raw(request: Request, cookie_name: str) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return request.cookies.get(cookie_name)


def decode_or_none(raw: str, secret: str, algorithm: str) -> dict | None:
    try:
        return jwt.decode(raw, secret, algorithms=[algorithm])
    except JWTError:
        return None
