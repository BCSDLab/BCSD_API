from io import BytesIO

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.svg import SvgPathImage


def generate(text: str, fmt: str, size: int) -> bytes:
    if fmt == "svg":
        return _generate_svg(text)
    return _generate_png(text, size)


def _generate_png(text: str, size: int) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(image_factory=StyledPilImage)
    img = img.resize((size, size))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_svg(text: str) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(image_factory=SvgPathImage)
    buf = BytesIO()
    img.save(buf)
    return buf.getvalue()
