_STATUS_LEVEL = {
    "General": 0, "Beginner": 1, "Regular": 2, "Mentor": 7,
}
_ROLE_LEVEL = {
    "edu_leader": 3, "track_leader": 4,
    "vice_president": 5, "president": 6,
}


def level(status: str, role: str | None) -> int:
    s = _STATUS_LEVEL.get(status, 0)
    r = _ROLE_LEVEL.get(role or "", 0)
    return max(s, r)
