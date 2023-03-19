import time

import anyio
import pytest

from starlette_web.common.caches.base import BaseCache
from starlette_web.tests.helpers import await_
from starlette_web.common.caches.base import CacheLockError


class BaseCacheTester:
    def _run_base_cache_test(self, cache: BaseCache):
        test_key = "b6e58cf5-4b83-400c-8c11-1dee87174200"
        await_(cache.async_delete(test_key))

        value = await_(cache.async_get(test_key))
        assert value is None

        value_obj = {
            "item_1": None,
            "item_2": True,
            "item_3": 432534523452345234523452435,
            "item_4": ["str", 12, None, True, {}],
            "item_5": {
                "item_5_1": False,
                "item_5_2": 34,
            },
        }

        await_(cache.async_set(test_key, value_obj, 0.2))
        value = await_(cache.async_get(test_key))
        assert value == value_obj
        assert await_(cache.async_has_key(test_key))

        time.sleep(0.3)
        value = await_(cache.async_get(test_key))
        assert value is None

    def _run_cache_many_ops_test(self, cache: BaseCache):
        test_key_1 = "2a8006ac-e296-486e-8044-b27517aaaaaa"
        test_key_2 = "2a8006ac-e296-486e-8044-b27517bbbbbb"

        await_(cache.async_delete_many([test_key_1, test_key_2]))

        keys = await_(cache.async_keys("2a8006ac-e296-486e-8044-b27517*"))
        assert len(keys) == 0

        await_(
            cache.async_set_many(
                {
                    test_key_1: 10,
                    test_key_2: 42,
                },
                timeout=0.2,
            )
        )

        keys = await_(cache.async_keys("2a8006ac-e296-486e-8044-b27517*"))
        assert len(keys) == 2

        values = await_(cache.async_get_many(keys))
        assert values == {
            test_key_1: 10,
            test_key_2: 42,
        }

        await_(cache.async_set(test_key_2, 1.0))
        time.sleep(0.3)

        keys = await_(cache.async_keys("2a8006ac-e296-486e-8044-b27517*"))
        assert len(keys) == 1

    def _run_cache_lock_test(self, cache: BaseCache):
        async def lock_checker():
            async with cache.lock("test_lock", timeout=0.5):
                await anyio.sleep(0.1)

        await_(lock_checker())

    def _run_cache_mutual_lock_test(self, cache: BaseCache):
        async def lock_checker():
            async with cache.lock("test_lock", timeout=0.2, blocking_timeout=0.1):
                async with cache.lock("test_lock", timeout=0.2, blocking_timeout=0.1):
                    await anyio.sleep(0.2)

        with pytest.raises(CacheLockError):
            await_(lock_checker())

    def _run_cache_timeouts_test(self, cache: BaseCache):
        timeout = 0.1
        number_of_tests = 4
        sleep_time = 0.2

        async def task_with_lock():
            async with cache.lock("test_lock", blocking_timeout=2.0, timeout=timeout):
                await anyio.sleep(sleep_time)

        start_time = time.time()

        async def gather_coroutines():
            async with anyio.create_task_group() as nursery:
                for _ in range(number_of_tests):
                    nursery.start_soon(task_with_lock)

        await_(gather_coroutines())
        end_time = time.time()
        run_time = end_time - start_time

        expected_runtime = (sleep_time + (number_of_tests - 1) * timeout)
        assert abs(run_time - expected_runtime) < 0.2
