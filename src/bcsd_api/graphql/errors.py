from graphql import GraphQLError
from pydantic import ValidationError
from strawberry.extensions import SchemaExtension

from bcsd_api.global_.exception.base import AppException


class AppErrorExtension(SchemaExtension):
    def on_operation(self):
        yield
        result = self.execution_context.result
        if not result:
            return
        if not result.errors:
            return
        result.errors = [_map_error(e) for e in result.errors]


def _map_error(err: GraphQLError) -> GraphQLError:
    orig = err.original_error
    if isinstance(orig, AppException):
        return _from_app(orig)
    if isinstance(orig, ValidationError):
        return _from_validation(orig)
    return err


def _from_app(exc: AppException) -> GraphQLError:
    return GraphQLError(
        message=exc.message,
        extensions={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
        },
    )


def _from_validation(exc: ValidationError) -> GraphQLError:
    return GraphQLError(
        message=str(exc),
        extensions={
            "error_code": "VALIDATION_ERROR",
            "status_code": 400,
        },
    )
