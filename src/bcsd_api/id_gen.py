import random
import string
from datetime import datetime, timezone, timedelta

_KST = timezone(timedelta(hours=9))


def generate_id(prefix: str) -> str:
    now = datetime.now(_KST)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{prefix}-{timestamp}-{suffix}"
