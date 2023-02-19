import time

from starlette_web.common.caches import caches
from starlette_web.tests.helpers import await_


locmem_cache = caches["locmem"]


class TestWebsocketEndpoint:
    def test_base_websocket_endpoint(self, client):
        await_(locmem_cache.async_clear())

        with client.websocket_connect("/ws/test_websocket_base") as websocket:
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert cache_keys == []

            websocket.send_json({"request_type": "test"})
            time.sleep(1)
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert len(cache_keys) == 1
            task_id = cache_keys[0]
            assert len(task_id) == 50

            time.sleep(2)
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert len(cache_keys) == 1
            assert cache_keys[0] == task_id + "_result"
            result_value = await_(locmem_cache.async_get(cache_keys[0]))
            assert result_value == "test"
