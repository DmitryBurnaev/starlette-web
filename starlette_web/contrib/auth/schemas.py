import typing
from marshmallow import Schema, ValidationError
from webargs import fields, validate


__all__ = [
    "SignInSchema",
    "SignUpSchema",
    "JWTResponseSchema",
    "UserResponseSchema",
    "RefreshTokenSchema",
    "ChangePasswordSchema",
    "UserInviteRequestSchema",
    "UserInviteResponseSchema",
    "ResetPasswordRequestSchema",
    "ResetPasswordResponseSchema",
]


class TwoPasswordsMixin:
    @staticmethod
    def is_valid(data: typing.Mapping) -> typing.Mapping:
        if data["password_1"] != data["password_2"]:
            msg = "Passwords must be equal"
            raise ValidationError(msg, data={"password_1": msg, "password_2": msg})

        return data


class SignInSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=2, max=32))


class SignUpSchema(TwoPasswordsMixin, Schema):
    email = fields.Email(required=True, validate=validate.Length(max=128))
    password_1 = fields.Str(required=True, validate=validate.Length(min=2, max=32))
    password_2 = fields.Str(required=True, validate=validate.Length(min=2, max=32))
    invite_token = fields.Str(required=True, validate=validate.Length(min=10, max=32))


class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True, validate=validate.Length(min=10, max=512))


class JWTResponseSchema(Schema):
    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=True)

    class Meta:
        fields = ("access_token", "refresh_token")


class UserInviteRequestSchema(Schema):
    email = fields.Email(required=True)


class UserInviteResponseSchema(Schema):
    id = fields.Int()
    email = fields.Email(required=True)
    token = fields.Str(required=True)
    expired_at = fields.DateTime(required=True)
    created_at = fields.DateTime(required=True)
    owner_id = fields.Int(required=True)


class ResetPasswordRequestSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordResponseSchema(Schema):
    user_id = fields.Int()
    email = fields.Email(required=True)
    token = fields.Str(required=True)


class ChangePasswordSchema(TwoPasswordsMixin, Schema):
    token = fields.Str(required=True, validate=validate.Length(min=1))
    password_1 = fields.Str(required=True, validate=validate.Length(min=2, max=32))
    password_2 = fields.Str(required=True, validate=validate.Length(min=2, max=32))


class UserResponseSchema(Schema):
    id = fields.Int(required=True)
    email = fields.Email(required=True)
    is_active = fields.Bool(required=True)
    is_superuser = fields.Bool(required=True)
