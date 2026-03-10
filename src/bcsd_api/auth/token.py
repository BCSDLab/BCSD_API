from datetime import datetime, timedelta, timezone

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
