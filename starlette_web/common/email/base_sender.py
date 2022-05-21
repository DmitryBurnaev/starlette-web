from typing import Optional, List


class BaseEmailSender:
    async def _open(self):
        return self

    async def _close(self):
        pass

    async def __aenter__(self):
        await self._open()
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
        raise NotImplementedError

    async def send_mass_email(
        self,
        subject: str,
        html_content: str,
        recipients_list: List[str],
        from_email: Optional[str] = None,
    ):
        raise NotImplementedError
