from bcsd_api.qr.service import generate


def test_generate_png():
    data = generate("hello", "png", 300)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_svg():
    data = generate("hello", "svg", 300)
    assert b"<svg" in data


def test_generate_korean():
    data = generate("한글 테스트", "png", 300)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
