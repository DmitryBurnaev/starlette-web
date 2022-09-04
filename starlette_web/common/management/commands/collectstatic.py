from importlib import import_module
from pathlib import Path
import shutil

from starlette_web.common.conf import settings
from starlette_web.common.management.base import BaseCommand


# TODO: enhance variability
# TODO: handle errors
class Command(BaseCommand):
    SKIP_APPS = ["starlette_web.common"]

    async def handle(self, **options):
        Path.mkdir(settings.TEMPLATES["ROOT_DIR"], exist_ok=True)
        Path.mkdir(settings.STATIC["ROOT_DIR"], exist_ok=True)

        for app_name in settings.INSTALLED_APPS:
            if app_name in self.SKIP_APPS:
                continue

            module = import_module(app_name)
            module_path = Path(module.__file__).parent

            await self.move_apps_static(module_path)
            await self.move_apps_templates(module_path)

    async def move_apps_static(self, apps_path: Path):
        static_dir = (apps_path / 'static')
        if static_dir.is_dir():
            for child in static_dir.iterdir():
                if child.is_file():
                    shutil.copyfile(child, settings.STATIC["ROOT_DIR"] / child.name)
                elif child.is_dir():
                    destination_dir = settings.STATIC["ROOT_DIR"] / child.name
                    if destination_dir.is_dir():
                        shutil.rmtree(destination_dir)
                    shutil.copytree(child, destination_dir)

    async def move_apps_templates(self, apps_path: Path):
        templates_dir = (apps_path / 'templates')
        if templates_dir.is_dir():
            for child in templates_dir.iterdir():
                if child.is_file():
                    shutil.copyfile(child, settings.TEMPLATES["ROOT_DIR"] / child.name)
                elif child.is_dir():
                    destination_dir = settings.TEMPLATES["ROOT_DIR"] / child.name
                    if destination_dir.is_dir():
                        shutil.rmtree(destination_dir)
                    shutil.copytree(child, destination_dir)
