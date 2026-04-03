from pathlib import Path

_DIR = Path(__file__).parent


def _load(name: str) -> str:
    return (_DIR / name).read_text()


def verify_body(code: str) -> str:
    return _load("verify.html").format(code=code)
