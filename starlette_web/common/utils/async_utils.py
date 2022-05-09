# https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/#cleanup-in-generators-and-async-generators  # noqa: E501
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
