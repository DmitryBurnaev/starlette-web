from starlette.templating import Jinja2Templates

from starlette_web.common.conf import settings


templates = Jinja2Templates(
    directory=settings.TEMPLATES["ROOT_DIR"],
    autoescape=settings.TEMPLATES["AUTOESCAPE"],
    auto_reload=settings.TEMPLATES["AUTORELOAD"],
)


TemplateResponse = templates.TemplateResponse
