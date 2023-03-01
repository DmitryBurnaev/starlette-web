# Modification of https://github.com/Woile/starlette-apispec/blob/master/starlette_apispec/schemas.py  # noqa: E501
from collections import deque
from typing import List

from apispec import APISpec
from apispec.exceptions import DuplicateComponentNameError
from starlette.routing import BaseRoute, Mount, Route
from starlette.schemas import BaseSchemaGenerator, EndpointInfo

from starlette_web.common.authorization.backends import BaseAuthenticationBackend
from starlette_web.common.http.schemas import get_error_schema_class
from starlette_web.common.i18n import gettext


# TODO: custom EndpointInfo with link to endpoint class
# TODO: maybe allow user to override class in settings (?)
class APISpecSchemaGenerator(BaseSchemaGenerator):
    ERROR_SCHEMA_NAME = "Error"

    def __init__(self, spec: APISpec) -> None:
        self.spec: APISpec = spec
        self.security_schemas = {}
        self.paths_and_endpoints = {}

    def _fetch_paths_and_endpoints(self, initial_routes: List[BaseRoute]):
        if self.paths_and_endpoints:
            return self.paths_and_endpoints

        mounts = deque([])
        routes = {}

        for route in initial_routes:
            # Skip any websocket connections
            if isinstance(route, Mount):
                mounts.append((self._remove_converter(route.path), route))
            elif isinstance(route, Route) and getattr(route, "include_in_schema", True):
                routes[self._remove_converter(route.path)] = route.endpoint

        while mounts:
            path, mount = mounts.popleft()
            for route in mount.routes:
                # Skip any websocket connections
                if isinstance(route, Mount):
                    mounts.append((path + self._remove_converter(route.path), route))
                elif isinstance(route, Route) and getattr(route, "include_in_schema", True):
                    routes[path + self._remove_converter(route.path)] = route.endpoint

        self.paths_and_endpoints = routes

    def _add_security_schema(self, auth_backend: BaseAuthenticationBackend) -> str:
        auth_name = getattr(auth_backend, "openapi_name", None) or auth_backend.__name__

        if auth_name in self.security_schemas:
            if self.security_schemas[auth_name] != auth_backend:
                raise DuplicateComponentNameError(
                    gettext("Duplicate auth_backend $auth_name", auth_name=auth_name)
                )
        else:
            self.security_schemas[auth_name] = auth_backend
            self.spec.components.security_scheme(auth_name, auth_backend.openapi_spec)

        return auth_name

    def _populate_security_schema(self, endpoint: EndpointInfo, parsed_docstring: dict):
        if parsed_docstring.get("security"):
            return

        kls = self.paths_and_endpoints[endpoint.path]
        if not getattr(kls, "auth_backend", None):
            return

        if getattr(kls.auth_backend, "openapi_spec", None):
            security_schema = self._add_security_schema(kls.auth_backend)
            # TODO: examine, if something should be passed into dict object
            parsed_docstring["security"] = [{security_schema: []}]

    def _populate_auth_errors(self, endpoint: EndpointInfo, parsed_docstring: dict):
        kls = self.paths_and_endpoints[endpoint.path]

        if getattr(kls, "auth_backend", None):
            parsed_docstring["responses"] = {
                **parsed_docstring.get("responses", {}),
                "401": {
                    "description": gettext("Authentication error."),
                    "content": {"application/json": {"schema": self.ERROR_SCHEMA_NAME}},
                },
            }

        if getattr(kls, "permission_classes", []):
            parsed_docstring["responses"] = {
                **parsed_docstring.get("responses", {}),
                "403": {
                    "description": gettext("Access forbidden."),
                    "content": {"application/json": {"schema": self.ERROR_SCHEMA_NAME}},
                },
            }

    def _populate_validation(self, endpoint: EndpointInfo, parsed_docstring: dict):
        if "requestBody" in parsed_docstring:
            parsed_docstring["responses"] = {
                **parsed_docstring.get("responses", {}),
                "400": {
                    "description": gettext("Bad Request."),
                    "content": {"application/json": {"schema": self.ERROR_SCHEMA_NAME}},
                },
            }

    def get_schema(self, routes: List[BaseRoute]) -> dict:
        ErrorResponseSchema = get_error_schema_class()()
        if self.ERROR_SCHEMA_NAME not in self.spec.components.schemas:
            self.spec.components.schema(self.ERROR_SCHEMA_NAME, schema=ErrorResponseSchema)

        endpoints = self.get_endpoints(routes)
        self._fetch_paths_and_endpoints(routes)

        for endpoint in endpoints:
            parsed = self.parse_docstring(endpoint.func)
            self._populate_security_schema(endpoint, parsed)
            self._populate_auth_errors(endpoint, parsed)
            self._populate_validation(endpoint, parsed)

            self.spec.path(
                path=endpoint.path,
                operations={endpoint.http_method: parsed},
            )

        return self.spec.to_dict()
