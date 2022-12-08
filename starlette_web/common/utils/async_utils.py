# https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/#cleanup-in-generators-and-async-generators  # noqa: E501
import asyncio
import logging
from typing import Coroutine, Any, TypeVar

T = TypeVar("T")


try:
    from contextlib import aclosing
except (ImportError, SystemError):

    class aclosing:
        def __init__(self, async_generator):
            self.async_generator = async_generator

        async def __aenter__(self):
            return self.async_generator

        async def __aexit__(self, *args):
            await self.async_generator.close()

            # Re-raise exception, if any
            return False


def create_task(
    coroutine: Coroutine[Any, Any, T],
    logger: logging.Logger,
    error_message: str = "",
    error_message_message_args: tuple[Any, ...] = (),
) -> asyncio.Task[T]:
    """Creates asyncio.Task from coro and provides logging for any exceptions"""

    def handle_task_result(cover_task: asyncio.Task) -> None:
        """Logging any exceptions after task finished"""
        try:
            cover_task.result()
        except asyncio.CancelledError:
            # Task cancellation should not be logged as an error.
            pass
        except Exception as exc:  # pylint: disable=broad-except
            if error_message:
                logger.exception(error_message, *error_message_message_args)
            else:
                logger.exception(f"Couldn't complete {coroutine.__name__}: %r", exc)

    task = asyncio.create_task(coroutine)
    task.add_done_callback(handle_task_result)
    return task
