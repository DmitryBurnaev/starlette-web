import json
from typing import Any

from starlette.responses import Response, BackgroundTask


class BaseRenderer(Response):
    pass


class JSONRenderer(BaseRenderer):
    # TODO: encode with custom JSONEncoder (imported from Django)
    json_encode_class = json.JSONEncoder
    media_type = "application/json"

    # Copied from starlette.responses.JSONResponse
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: Any) -> bytes:
        return json.dumps(
            self.preprocess_content(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=self.json_encode_class,
        ).encode("utf-8")

    @staticmethod
    def preprocess_content(content):
        return content
