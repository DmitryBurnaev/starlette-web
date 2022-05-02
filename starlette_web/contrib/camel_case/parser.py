from typing import Optional, Mapping

from webargs_starlette import StarletteParser

from starlette_web.contrib.camel_case.utils import underscoreize


class CamelCaseStarletteParser(StarletteParser):
    async def parse(self, *args, **kwargs) -> Optional[Mapping]:
        json_data = await super().parse(*args, **kwargs)
        return underscoreize(json_data)
