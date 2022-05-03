from starlette_web.common.http.renderers import JSONRenderer
from starlette_web.contrib.camel_case.utils import camelize


class CamelCaseJSONRenderer(JSONRenderer):
    @staticmethod
    def preprocess_content(content):
        return camelize(content)
