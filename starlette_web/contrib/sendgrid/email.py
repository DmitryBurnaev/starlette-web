import logging
from typing import Optional, List

import httpx

from starlette_web.common.email import BaseEmailSender, EmailSenderError
from starlette_web.common.http.statuses import status_is_success
from starlette_web.core import settings


class SendgridAPIEmailSender(BaseEmailSender):
    def __init__(self):
        self.request_url = f"https://api.sendgrid.com/{settings.SENDGRID_API_VERSION}/mail/send"
        self.request_header = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"}
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _get_request_data(subject: str, html_content: str, to_email: str):
        return {
            "personalizations": [{"to": [{"email": to_email}], "subject": subject}],
            "from": {"email": settings.EMAIL_FROM},
            "content": [{"type": "text/html", "value": html_content}],
        }

    async def send_email(
        self,
        subject: str,
        html_content: str,
        to_email: str,
        from_email: Optional[str] = None,
    ):
        request_data = self._get_request_data(subject, html_content, to_email)
        self.logger.info("Send request to %s. Data: %s", self.request_url, request_data)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.request_url, json=request_data, headers=self.request_header
            )
            status_code = response.status_code
            if not status_is_success(status_code):
                response_text = response.json()
                raise EmailSenderError(
                    message=f"Couldn't send email to {to_email}",
                    details=f"Got status code: {status_code}; response text: {response_text}",
                    request_url=self.request_url,
                )
            else:
                self.logger.info("Email sent to %s. Status code: %s", to_email, status_code)

    async def send_mass_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        for to_email in recipients_list:
            await self.send_email(subject, html_content, to_email, from_email=from_email)
