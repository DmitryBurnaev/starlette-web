from typing import Optional, List


class EmailSenderError(Exception):
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ):
        self.message = message or ""
        self.details = details or ""

    def to_dict(self):
        return {
            "details": self.details,
            "message": self.message,
        }


class BaseEmailSender:
    async def _open(self):
        return self

    async def _close(self):
        pass

    async def __aenter__(self):
        try:
            await self._open()
        except Exception:
            await self._close()
            raise
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

        # Re-raise exception, if any
        return False

    async def send_email(
        self,
        subject: str,
        html_content: str,
        to_email: str,
        from_email: Optional[str] = None,
    ):
        await self.send_mass_email(subject, html_content, [to_email], from_email=from_email)

    async def send_mass_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        raise NotImplementedError
