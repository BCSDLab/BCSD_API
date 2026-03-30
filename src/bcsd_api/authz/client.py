from authzed.api.v1 import (
    CheckPermissionRequest,
    CheckPermissionResponse,
    Client,
    ObjectReference,
    Relationship,
    RelationshipUpdate,
    SubjectReference,
    WriteRelationshipsRequest,
    WriteSchemaRequest,
)
from grpcutil import insecure_bearer_token_credentials

_TOUCH = RelationshipUpdate.Operation.OPERATION_TOUCH
_DELETE = RelationshipUpdate.Operation.OPERATION_DELETE
_HAS = CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION


def _object_ref(obj_type: str, obj_id: str) -> ObjectReference:
    return ObjectReference(object_type=obj_type, object_id=obj_id)


def _subject_ref(user_id: str) -> SubjectReference:
    return SubjectReference(object=_object_ref("user", user_id))


def _relationship(res_type: str, res_id: str, relation: str, user_id: str) -> Relationship:
    return Relationship(
        resource=_object_ref(res_type, res_id),
        relation=relation,
        subject=_subject_ref(user_id),
    )


def _update(operation, res_type: str, res_id: str, relation: str, user_id: str) -> RelationshipUpdate:
    return RelationshipUpdate(
        operation=operation,
        relationship=_relationship(res_type, res_id, relation, user_id),
    )


def _resolve(call):
    resolve = getattr(call, "result", None)
    if resolve:
        return resolve()
    return call


class AuthzClient:
    def __init__(self, endpoint: str, token: str):
        self._client = Client(
            endpoint,
            insecure_bearer_token_credentials(token),
        )

    def check(self, res_type: str, res_id: str, permission: str, user_id: str) -> bool:
        call = self._client.CheckPermission(
            CheckPermissionRequest(
                resource=_object_ref(res_type, res_id),
                permission=permission,
                subject=_subject_ref(user_id),
            )
        )
        resp = _resolve(call)
        return resp.permissionship == _HAS

    def add_relation(self, res_type: str, res_id: str, relation: str, user_id: str) -> None:
        self._write(_TOUCH, res_type, res_id, relation, user_id)

    def remove_relation(self, res_type: str, res_id: str, relation: str, user_id: str) -> None:
        self._write(_DELETE, res_type, res_id, relation, user_id)

    def write_schema(self, schema: str) -> None:
        _resolve(self._client.WriteSchema(WriteSchemaRequest(schema=schema)))

    def _write(self, operation: int, res_type: str, res_id: str, relation: str, user_id: str) -> None:
        _resolve(self._client.WriteRelationships(
            WriteRelationshipsRequest(updates=[_update(operation, res_type, res_id, relation, user_id)])
        ))
