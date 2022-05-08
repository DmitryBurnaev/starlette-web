import httpx
import logging

from starlette_web.core import settings
from starlette_web.common.http.exceptions import SendRequestError
from starlette_web.common.http.statuses import status_is_success


# TODO: refactor completely
async def send_email(recipient_email: str, subject: str, html_content: str):
    """Allows sending email via Sendgrid API"""

    request_url = f"https://api.sendgrid.com/{settings.SENDGRID_API_VERSION}/mail/send"
    request_data = {
        "personalizations": [{"to": [{"email": recipient_email}], "subject": subject}],
        "from": {"email": settings.EMAIL_FROM},
        "content": [{"type": "text/html", "value": html_content}],
    }
    request_header = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"}
    request_logger = logging.getLogger(__name__)
    request_logger.info("Send request to %s. Data: %s", request_url, request_data)

    async with httpx.AsyncClient() as client:
        response = await client.post(request_url, json=request_data, headers=request_header)
        status_code = response.status_code
        if not status_is_success(status_code):
            response_text = response.json()
            raise SendRequestError(
                message=f"Couldn't send email to {recipient_email}",
                details=f"Got status code: {status_code}; response text: {response_text}",
                request_url=request_url,
            )
        else:
            request_logger.info("Email sent to %s. Status code: %s", recipient_email, status_code)
