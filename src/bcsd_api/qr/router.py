from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from bcsd_api.dependencies import current_user

from . import service
from .schema import QrParams

router = APIRouter(prefix="/v1/qr", tags=["qr"])

_MEDIA_TYPES = {"png": "image/png", "svg": "image/svg+xml"}


@router.get("")
def generate_qr(
    params: QrParams = Depends(),
    _: dict = Depends(current_user),
) -> StreamingResponse:
    data = service.generate(params.text, params.format, params.size)
    media = _MEDIA_TYPES[params.format]
    return StreamingResponse(BytesIO(data), media_type=media)
