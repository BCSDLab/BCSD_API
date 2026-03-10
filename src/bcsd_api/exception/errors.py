from .base import AppException


class NotFound(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "resource not found"


class Conflict(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "resource already exists"


class Unauthorized(AppException):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "authentication required"


class BadRequest(AppException):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "bad request"
