from typing import Type

from marshmallow import Schema, fields

from starlette_web.common.conf import settings
from starlette_web.common.utils import import_string


__ERROR_RESPONSE_SCHEMA = None


class ErrorDetailsSchema(Schema):
    error = fields.String(required=True, allow_none=False)
    details = fields.Raw(required=False, allow_none=True)


class ErrorResponseSchema(Schema):
    payload = fields.Nested(ErrorDetailsSchema, required=True)
    status = fields.String(required=False, allow_none=False)


def get_error_schema_class() -> Type[Schema]:
    global __ERROR_RESPONSE_SCHEMA
    if __ERROR_RESPONSE_SCHEMA is not None:
        return __ERROR_RESPONSE_SCHEMA

    __ERROR_RESPONSE_SCHEMA = import_string(settings.ERROR_RESPONSE_SCHEMA)
    return __ERROR_RESPONSE_SCHEMA
