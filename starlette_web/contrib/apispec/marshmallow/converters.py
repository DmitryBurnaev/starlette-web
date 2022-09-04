import json

from apispec.ext.marshmallow import OpenAPIConverter
from apispec.ext.marshmallow.field_converter import DEFAULT_FIELD_MAPPING
import marshmallow

from starlette_web.common.utils.json import StarletteJSONEncoder


# TODO: maybe allow user to override class in settings (?)
class StarletteWebMarshmallowOpenAPIConverter(OpenAPIConverter):
    # Decimal has no specific representation in OpenAPI standard
    # Support decimal representation in a same way, as drf-yasg does for Django
    # https://github.com/axnsan12/drf-yasg/blob/b99306f71c6a5779b62189df7d9c1f5ea1c794ef/src/drf_yasg/openapi.py#L48  # noqa: E501
    field_mapping = {
        **DEFAULT_FIELD_MAPPING,
        marshmallow.fields.Decimal: ("string", "decimal"),
    }

    def field2choices(self, field, **kwargs):
        res = super().field2choices(field, **kwargs)
        return json.loads(StarletteJSONEncoder().encode(res))

    def fields2jsonschema(self, fields, *, partial=None):
        res = super().fields2jsonschema(fields, partial=partial)

        # TODO: this field must be redefined to support changes to schema via renderer_class, i.e.
        """
        if 'required' in res and type(res['required']) is list:
            res['required'] = [camelize_key(d) for d in res['required']]
        if res.get('properties'):
            res['properties'] = camelize(res['properties'])
        return camelize(res)
        """
        return res
