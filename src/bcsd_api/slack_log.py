import json
import logging
import traceback
from urllib.request import Request, urlopen

SLACK_API = "https://slack.com/api/chat.postMessage"


class SlackHandler(logging.Handler):
    def __init__(self, token: str, channel: str):
        super().__init__()
        self._token = token
        self._channel = channel

    def emit(self, record):
        _send(self._token, self._channel, record)


def _format(record):
    text = f"*[{record.levelname}]* `{record.name}`\n{record.getMessage()}"
    if not record.exc_info:
        return text
    tb = "".join(traceback.format_exception(*record.exc_info))
    return text + f"\n```{tb}```"


def _send(token, channel, record):
    text = _format(record)
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
    payload = json.dumps({"channel": channel, "blocks": blocks}).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = Request(SLACK_API, data=payload, headers=headers)
    try:
        urlopen(req, timeout=5)
    except Exception:
        pass


def setup(token: str, channel: str):
    if not token or not channel:
        return
    handler = SlackHandler(token, channel)
    handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(handler)
