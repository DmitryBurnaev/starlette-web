from importlib import import_module
from pathlib import Path
import shutil

from starlette_web.common.conf import settings
from starlette_web.common.management.base import BaseCommand, CommandError


# TODO: enhance variability
# TODO: handle errors
# TODO: probably need refactoring ?
class Command(BaseCommand):
    help = (
        "Move static files and templates from INSTALLED_APPS "
        "directories to static root and templates root, respectively"
    )
    SKIP_APPS = ["starlette_web.common", "starlette_web.contrib.admin"]

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

        if "starlette_web.contrib.admin" in settings.INSTALLED_APPS:
            await self.move_admin_files()

    async def move_apps_static(self, apps_path: Path):
        static_dir = apps_path / "static"
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
        templates_dir = apps_path / "templates"
        if templates_dir.is_dir():
            for child in templates_dir.iterdir():
                if child.is_file():
                    shutil.copyfile(child, settings.TEMPLATES["ROOT_DIR"] / child.name)
                elif child.is_dir():
                    destination_dir = settings.TEMPLATES["ROOT_DIR"] / child.name
                    if destination_dir.is_dir():
                        shutil.rmtree(destination_dir)
                    shutil.copytree(child, destination_dir)

    async def move_admin_files(self):
        # This is special case, since starlette_admin package manages
        # static files in a bit different way
        try:
            module = import_module("starlette_admin")
        except (ImportError, SystemError) as exc:
            raise CommandError(details=str(exc)) from exc

        module_path = Path(module.__file__).parent
        module_static_dir = module_path / "statics"
        module_templates_dir = module_path / "templates"

        if not module_static_dir.is_dir():
            raise CommandError(details="Invalid structure of starlette_admin")
        if not module_templates_dir.is_dir():
            raise CommandError(details="Invalid structure of starlette_admin")

        target_static_dir = settings.STATIC["ROOT_DIR"] / "admin"
        target_templates_dir = settings.TEMPLATES["ROOT_DIR"] / "admin"

        Path(target_static_dir).mkdir(exist_ok=True)
        Path(target_templates_dir).mkdir(exist_ok=True)

        for child in module_static_dir.iterdir():
            if child.is_file():
                shutil.copyfile(child, target_static_dir / child.name)
            elif child.is_dir():
                destination_dir = target_static_dir / child.name
                if destination_dir.is_dir():
                    shutil.rmtree(destination_dir)
                shutil.copytree(child, destination_dir)

        for child in module_templates_dir.iterdir():
            if child.is_file():
                shutil.copyfile(child, target_templates_dir / child.name)
            elif child.is_dir():
                destination_dir = target_templates_dir / child.name
                if destination_dir.is_dir():
                    shutil.rmtree(destination_dir)
                shutil.copytree(child, destination_dir)
