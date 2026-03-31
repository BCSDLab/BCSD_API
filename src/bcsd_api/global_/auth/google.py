from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from bcsd_api.global_.exception import Unauthorized


def verify_token(token: str, client_id: str) -> dict:
    try:
        payload = id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
    except ValueError:
        raise Unauthorized("invalid google token")
    return {"email": payload["email"], "name": payload.get("name", "")}
