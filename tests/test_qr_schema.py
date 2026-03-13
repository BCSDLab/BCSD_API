import pytest
from pydantic import ValidationError

from bcsd_api.qr.schema import QrParams


def test_qr_params_defaults():
    params = QrParams(text="hello")
    assert params.format == "png"
    assert params.size == 300


def test_qr_params_svg():
    params = QrParams(text="hello", format="svg", size=500)
    assert params.format == "svg"
    assert params.size == 500


def test_qr_params_invalid_format():
    with pytest.raises(ValidationError):
        QrParams(text="hello", format="gif")


def test_qr_params_size_too_small():
    with pytest.raises(ValidationError):
        QrParams(text="hello", size=50)


def test_qr_params_size_too_large():
    with pytest.raises(ValidationError):
        QrParams(text="hello", size=1500)


def test_qr_params_text_too_long():
    with pytest.raises(ValidationError):
        QrParams(text="a" * 2001)
