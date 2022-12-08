from marshmallow import fields, Schema


class WSHeadersRequestSchema(Schema):
    authorization = fields.Str(data_key="Authorization")


class WSRequestAuthSchema(Schema):
    headers = fields.Nested(WSHeadersRequestSchema())
