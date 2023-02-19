import anyio

from sqlalchemy.ext.asyncio import AsyncSession


class AtomicTransaction:
    """
    Asynchronous wrapper around sqlalchemy.Session.begin_nested, that also commits/rollbacks at end
    """

    EXIT_MAX_DELAY: float = 60

    def __init__(self, db_session: AsyncSession, db_commit=True, **kwargs):
        self.db_session = db_session
        self.nested_block_wrapper = None
        self.nested_block = None
        self.db_commit = db_commit
        self.kwargs = kwargs

    async def __aenter__(self):
        self.nested_block_wrapper = self.db_session.begin_nested(**self.kwargs)
        self.nested_block = await self.nested_block_wrapper.__aenter__()
        return self.nested_block

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with anyio.fail_after(self.EXIT_MAX_DELAY, shield=True):
            if self.nested_block_wrapper:
                if exc_type is not None:
                    await self.nested_block.rollback()
                elif self.db_commit:
                    await self.nested_block.commit()

                await self.nested_block_wrapper.__aexit__(exc_type, exc_val, exc_tb)

        return False
