from starlette_web.tests.api.test_base import BaseTestAPIView

REFERENCE_SCHEMA = {
    "info": {
        "description": "My custom project.",
        "title": "Project documentation",
        "version": "0.0.1",
    },
    "paths": {
        "/api/auth/me/": {
            "get": {
                "description": "Profile info",
                "responses": {
                    "200": {
                        "description": "Profile",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "Authentication error.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
                "security": [{"JWTAuth": []}],
            }
        },
        "/api/auth/sign-in/": {
            "post": {
                "description": "Sign in",
                "requestBody": {
                    "required": True,
                    "description": "Sign in",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/SignIn"}}
                    },
                },
                "responses": {
                    "200": {
                        "description": "JsonWebToken",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JWTResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "Authentication failed",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
            }
        },
        "/api/auth/sign-up/": {
            "post": {
                "description": "Sign up",
                "requestBody": {
                    "required": True,
                    "description": "Sign up",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/SignUp"}}
                    },
                },
                "responses": {
                    "200": {
                        "description": "JsonWebToken",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JWTResponse"}
                            }
                        },
                    },
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
            }
        },
        "/api/auth/sign-out/": {
            "delete": {
                "description": "Sign out",
                "responses": {
                    "200": {"description": "Signed out"},
                    "401": {
                        "description": "Authentication error.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
                "security": [{"JWTAuth": []}],
            }
        },
        "/api/auth/refresh-token/": {
            "post": {
                "description": "Update refresh token",
                "requestBody": {
                    "required": True,
                    "description": "Refresh token",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/RefreshToken"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "JsonWebToken",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JWTResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "Authentication failed",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
            }
        },
        "/api/auth/invite-user/": {
            "post": {
                "description": "Invite user",
                "requestBody": {
                    "required": True,
                    "description": "Invited user's credentials",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/UserInviteRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Invited user",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInviteResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "Authentication error.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
                "security": [{"JWTAuth": []}],
            }
        },
        "/api/auth/reset-password/": {
            "post": {
                "description": "Reset password",
                "requestBody": {
                    "required": True,
                    "description": "User credentials",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResetPasswordRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Link to email",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ResetPasswordResponse"}
                            }
                        },
                    },
                    "401": {
                        "description": "Authentication error.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                    "403": {
                        "description": "Access forbidden.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
                "security": [{"JWTAuth": []}],
            }
        },
        "/api/auth/change-password/": {
            "post": {
                "description": "Change password",
                "requestBody": {
                    "required": True,
                    "description": "New password confirmation",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ChangePassword"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "New tokens",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/JWTResponse"}
                            }
                        },
                    },
                    "401": {"description": "Authentication failed"},
                    "400": {
                        "description": "Bad Request.",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                        },
                    },
                },
                "tags": ["Authorization"],
            }
        },
        "/health_check/": {
            "get": {
                "description": "Health check of services",
                "responses": {
                    "200": {
                        "description": "Services with status",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthCheck"}
                            }
                        },
                    },
                    "503": {"description": "Service unavailable"},
                },
                "tags": ["Health check"],
            }
        },
        "/sentry_check/": {
            "get": {
                "description": "Health check of Sentry logger",
                "responses": {"500": {"description": "Application error"}},
                "tags": ["Health check"],
            }
        },
    },
    "openapi": "3.0.2",
    "components": {
        "schemas": {
            "ErrorDetails": {
                "type": "object",
                "properties": {"error": {"type": "string"}, "details": {"nullable": True}},
                "required": ["error"],
            },
            "Error": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "payload": {"$ref": "#/components/schemas/ErrorDetails"},
                },
                "required": ["payload"],
            },
            "UserResponse": {
                "type": "object",
                "properties": {
                    "is_active": {"type": "boolean"},
                    "is_superuser": {"type": "boolean"},
                    "email": {"type": "string", "format": "email"},
                    "id": {"type": "integer"},
                },
                "required": ["email", "id", "is_active", "is_superuser"],
            },
            "SignIn": {
                "type": "object",
                "properties": {
                    "password": {"type": "string", "minLength": 2, "maxLength": 32},
                    "email": {"type": "string", "format": "email"},
                },
                "required": ["email", "password"],
            },
            "JWTResponse": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                },
                "required": ["access_token", "refresh_token"],
            },
            "SignUp": {
                "type": "object",
                "properties": {
                    "invite_token": {"type": "string", "minLength": 10, "maxLength": 32},
                    "password_2": {"type": "string", "minLength": 2, "maxLength": 32},
                    "password_1": {"type": "string", "minLength": 2, "maxLength": 32},
                    "email": {"type": "string", "format": "email", "maxLength": 128},
                },
                "required": ["email", "invite_token", "password_1", "password_2"],
            },
            "RefreshToken": {
                "type": "object",
                "properties": {
                    "refresh_token": {"type": "string", "minLength": 10, "maxLength": 512}
                },
                "required": ["refresh_token"],
            },
            "UserInviteRequest": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
                "required": ["email"],
            },
            "UserInviteResponse": {
                "type": "object",
                "properties": {
                    "owner_id": {"type": "integer"},
                    "email": {"type": "string", "format": "email"},
                    "expired_at": {"type": "string", "format": "date-time"},
                    "id": {"type": "integer"},
                    "token": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
                "required": ["created_at", "email", "expired_at", "owner_id", "token"],
            },
            "ResetPasswordRequest": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
                "required": ["email"],
            },
            "ResetPasswordResponse": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "user_id": {"type": "integer"},
                },
                "required": ["email", "token"],
            },
            "ChangePassword": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "minLength": 1},
                    "password_2": {"type": "string", "minLength": 2, "maxLength": 32},
                    "password_1": {"type": "string", "minLength": 2, "maxLength": 32},
                },
                "required": ["password_1", "password_2", "token"],
            },
            "ServicesCheck": {"type": "object", "properties": {"postgres": {"type": "string"}}},
            "HealthCheck": {
                "type": "object",
                "properties": {
                    "errors": {"type": "array", "items": {"type": "string"}},
                    "services": {"$ref": "#/components/schemas/ServicesCheck"},
                },
            },
        },
        "securitySchemes": {"JWTAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
    },
}


class TestOpenAPISchema(BaseTestAPIView):
    url = "/openapi/schema/"

    def test_schema(self, client, user):
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json() == REFERENCE_SCHEMA
