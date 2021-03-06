from typing import Optional, List

from starlette_web.common.email.base_sender import BaseEmailSender
from starlette_web.common.exceptions import ImproperlyConfigured
from starlette_web.common.utils.importing import import_string
from starlette_web.core import settings


class EmailManager:
    sender: Optional[BaseEmailSender] = None

    def _switch_to_email_sender_class(self, import_path: str):
        try:
            self.sender = import_string(import_path)()
        except (ImportError, SystemError, TypeError):
            raise ImproperlyConfigured(
                "settings.EMAIL_SENDER is not a valid import path to a callable"
            )

        if not isinstance(self.sender, BaseEmailSender):
            raise ImproperlyConfigured(
                "Class, specified with settings.EMAIL_SENDER, "
                "is not a subclass of BaseEmailSender"
            )

    def _get_email_sender(self) -> BaseEmailSender:
        if self.sender:
            return self.sender

        if not hasattr(settings, "EMAIL_SENDER"):
            raise ImproperlyConfigured("In order to send emails, settings.EMAIL_SENDER must be set")

        self._switch_to_email_sender_class(settings.EMAIL_SENDER)
        return self.sender

    async def send_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        async with self._get_email_sender() as sender:
            await sender.send_email(subject, html_content, recipients_list, from_email=from_email)


_email_manager = EmailManager()
send_email = _email_manager.send_email
