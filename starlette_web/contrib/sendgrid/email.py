import logging
from typing import Optional, List

import httpx

from starlette_web.common.conf import settings
from starlette_web.common.email import BaseEmailSender, EmailSenderError
from starlette_web.common.http.statuses import status_is_success


logger = logging.getLogger(__name__)


class SendgridAPIEmailSender(BaseEmailSender):
    def __init__(self):
        self.request_url = f"https://api.sendgrid.com/{settings.SENDGRID_API_VERSION}/mail/send"
        self.request_header = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"}
        self.client: Optional[httpx.AsyncClient] = None

    @staticmethod
    def _get_request_data(
        subject: str, html_content: str, recipients_list: List[str], from_email: str
    ):
        return {
            "personalizations": [
                {
                    "to": [{"email": email} for email in recipients_list],
                    "subject": subject,
                },
            ],
            "from": {
                "email": from_email,
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content,
                },
            ],
        }

    async def _open(self):
        self.client = await httpx.AsyncClient().__aenter__()

    async def _close(self):
        if self.client:
            await self.client.aclose()
        self.client = None

    async def send_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        from_email = from_email or settings.EMAIL_FROM
        request_data = self._get_request_data(subject, html_content, recipients_list, from_email)
        logger.info("Send request to %s. Data: %s", self.request_url, request_data)

        response = await self.client.post(
            self.request_url, json=request_data, headers=self.request_header
        )
        status_code = response.status_code

        if not status_is_success(status_code):
            response_text = response.json()
            raise EmailSenderError(
                message=f"Couldn't send email to {recipients_list}",
                details=f"Got status code: {status_code}; response text: {response_text}",
            )
        else:
            logger.info("Email sent to %s. Status code: %s", recipients_list, status_code)
