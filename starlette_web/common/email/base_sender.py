from typing import Optional, List

import anyio

from starlette_web.common.http.exceptions import BaseApplicationError


class EmailSenderError(BaseApplicationError):
    pass


class BaseEmailSender:
    MAX_BULK_SIZE = 1
    EXIT_MAX_DELAY = 60

    async def _open(self):
        return self

    async def _close(self):
        pass

    async def __aenter__(self):
        try:
            await self._open()
        except Exception as exc:
            with anyio.fail_after(self.EXIT_MAX_DELAY, shield=True):
                await self._close()
            raise EmailSenderError(details=str(exc)) from exc

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with anyio.fail_after(self.EXIT_MAX_DELAY, shield=True):
            await self._close()

        if exc_type:
            raise EmailSenderError(details=str(exc_val)) from exc_val

    async def send_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        raise NotImplementedError
