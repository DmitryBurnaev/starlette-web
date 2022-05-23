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
        except Exception as exc:
            await self._close()

            message = f"{type(exc)}: {exc}"
            new_exc = EmailSenderError(message=message)
            new_exc.__cause__ = exc
            raise new_exc

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

        if exc_type:
            message = f"{exc_type}: {exc_val}"
            new_exc = EmailSenderError(message=message)
            new_exc.__cause__ = exc_val
            raise new_exc

    async def send_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        raise NotImplementedError
