import uuid

from starlette_web.common.management.base import BaseCommand
from starlette_web.contrib.auth.models import User


class Command(BaseCommand):
    help = "Command to test database connection"

    async def handle(self, **options):
        test_user_password = str(uuid.uuid4())
        email = str(uuid.uuid4()).replace("-", "") + "@test.com"
        password = User.make_password(test_user_password)

        async with self.app.session_maker() as session:
            user = await User.async_create(session, email=email, password=password)

            await User.async_delete(session, {"id": user.id})
            await session.commit()
