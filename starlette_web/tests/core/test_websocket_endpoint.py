import time
import pytest

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

    def test_multiple_tasks_spawn(self, client):
        await_(locmem_cache.async_clear())

        with client.websocket_connect("/ws/test_websocket_base") as websocket:
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert cache_keys == []

            websocket.send_json({"request_type": "test_1"})
            websocket.send_json({"request_type": "test_2"})
            websocket.send_json({"request_type": "test_3"})

            time.sleep(3)
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert len(cache_keys) == 3
            results = await_(locmem_cache.async_get_many(cache_keys))
            assert set([value for key, value in results.items()]) == {"test_1", "test_2", "test_3"}

    def test_cancelled_task(self, client):
        await_(locmem_cache.async_clear())

        with client.websocket_connect("/ws/test_websocket_cancel") as websocket:
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert cache_keys == []

            websocket.send_json({"request_type": "test_1"})
            websocket.send_json({"request_type": "test_2"})
            websocket.send_json({"request_type": "cancel"})

            time.sleep(3)
            cache_keys = await_(locmem_cache.async_keys("*"))
            assert len(cache_keys) == 2
            results = await_(locmem_cache.async_get_many(cache_keys))
            assert set([value for key, value in results.items()]) == {"test_1", "test_2"}

    def test_failed_task(self, client_ws_fail):
        await_(locmem_cache.async_clear())

        # Exception is raised by client_ws_fail,
        # due to raised Exception in 3rd background task
        with pytest.raises(Exception):
            with client_ws_fail.websocket_connect("/ws/test_websocket_cancel") as websocket:
                cache_keys = await_(locmem_cache.async_keys("*"))
                assert cache_keys == []

                websocket.send_json({"request_type": "test_1"})
                websocket.send_json({"request_type": "test_2"})
                websocket.send_json({"request_type": "fail"})

                time.sleep(3)

        cache_keys = await_(locmem_cache.async_keys("*"))
        assert len(cache_keys) == 1
        assert cache_keys[0].endswith("_exception")
        result_value = await_(locmem_cache.async_get(cache_keys[0]))
        assert result_value == "fail"
