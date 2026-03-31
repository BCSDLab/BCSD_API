import resend


class ResendSender:
    def __init__(self, api_key: str, sender: str):
        resend.api_key = api_key
        self._sender = sender

    def send(self, to: str, subject: str, body: str) -> None:
        resend.Emails.send({
            "from": self._sender,
            "to": [to],
            "subject": subject,
            "html": body,
        })
