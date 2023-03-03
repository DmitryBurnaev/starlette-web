from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import (
    OpenAPIValidationError, OpenAPISpecValidatorError,
)
from traceback_with_variables import format_exc

from starlette_web.common.conf import settings
from starlette_web.common.conf.base_app_config import BaseAppConfig
from starlette_web.common.http.exceptions import ImproperlyConfigured
from starlette_web.common.utils import import_string
from starlette_web.contrib.apispec.views import schemas


class AppConfig(BaseAppConfig):
    app_name = "apispec"

    def perform_checks(self):
        routes = import_string(settings.ROUTES)

        try:
            # This check mostly fails on invalid indentation
            # or partially missing properties.
            api_spec = schemas.get_schema(routes)
        except Exception as exc:  # noqa
            # Printing variable values in traceback is the only
            # viable way to know which schema is fallible
            raise ImproperlyConfigured(
                message="Invalid schema in apispec",
                details=format_exc(exc, num_skipped_frames=0),
            )

        try:
            # This check finds missing whole blocks,
            # i.e. missing info about path parameter in schema
            validate_spec(api_spec)
        except (OpenAPIValidationError, OpenAPISpecValidatorError) as exc:
            raise ImproperlyConfigured(
                details=str(exc),
            )
