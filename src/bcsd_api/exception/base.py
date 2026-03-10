class AppException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "internal server error"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)
