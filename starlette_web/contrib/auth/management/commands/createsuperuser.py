from starlette_web.common.management.base import BaseCommand, CommandError
from starlette_web.contrib.auth.models import User
from starlette_web.contrib.auth.management.auth_command_mixin import AuthCommandMixin


class Command(AuthCommandMixin, BaseCommand):
    help = "Create a User (contrib.auth) with superuser privileges"

    async def handle(self, **options):
        async with self.app.session_maker() as session:
            email = self.get_input_data("Input email (username): ")
            self.validate_field("email", email)
            user = await User.async_get(db_session=session, email=email)
            if user is not None:
                raise CommandError(details=f"User with email = {email} already exists.")

            password_1 = self.get_input_data("Input password: ")
            self.validate_field("password", password_1)
            password_2 = self.get_input_data("Retype password: ")
            if password_1 != password_2:
                raise CommandError(details="Password mismatch.")

            user = await User.async_create(
                db_session=session,
                db_commit=True,
                email=email,
                password=User.make_password(password_1),
                is_superuser=True,
                is_active=True,
            )

            # TODO: use logging ?
            print(f"User {user} created successfully.")
