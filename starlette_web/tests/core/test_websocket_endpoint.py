import anyio
import time
import pytest

from starlette.websockets import WebSocketDisconnect

from starlette_web.common.caches import caches
from starlette_web.contrib.auth.utils import encode_jwt
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

    def test_failed_task(self, client):
        await_(locmem_cache.async_clear())

        # Exception is raised by client_ws_fail,
        # due to raised Exception in 3rd background task
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/test_websocket_cancel") as websocket:
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

    def test_authentication_failure(self, client):
        await_(locmem_cache.async_clear())

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/test_websocket_auth") as websocket:
                websocket.send_json({"request_type": "test_1"})
                time.sleep(3)

    def test_authentication_success(self, client, dbs, user, user_session):
        await_(locmem_cache.async_clear())

        jwt, _ = encode_jwt({"user_id": user.id, "session_id": user_session.public_id})
        headers = {"authorization": f"Bearer {jwt}".encode("latin-1")}

        with client.websocket_connect("/ws/test_websocket_auth", headers=headers) as websocket:
            websocket.send_json({"request_type": "test_1"})
            time.sleep(3)

            cache_keys = await_(locmem_cache.async_keys("*"))
            assert len(cache_keys) == 1
            results = await_(locmem_cache.async_get_many(cache_keys))
            assert set([value for key, value in results.items()]) == {"test_1"}

    def test_finite_periodic_task(self, client):
        await_(locmem_cache.async_clear())

        # Only async operations allow to be run with a timeout wrapper in Python
        async def _wait_for_response(ws, timeout):
            def cancellable_ws_receive_json(timeout):
                # ws.receive() does not provide a "timeout" parameter
                # without a timeout, websocket will try to get message indefinitely
                # It is also not possible to finish a thread with synchronous infinite loop
                # whereas we may not call anyio.to_process due to websocket being unpicklable
                return ws._send_queue.get(block=True, timeout=timeout)

            with anyio.fail_after(delay=timeout):
                return await anyio.to_thread.run_sync(cancellable_ws_receive_json, timeout + 1)

        with client.websocket_connect("/ws/test_websocket_finite_periodic") as websocket:
            websocket.send_json({"request_type": "periodic"})
            for i in range(4):
                response = websocket.receive_json()
                assert response["response"] == i

            # Websocket handler only sends message 4 times,
            # so next receive() should hang forever, unless one enforces timeout
            with pytest.raises(TimeoutError):
                await_(_wait_for_response(websocket, 2))

    def test_multiple_infinite_tasks(self, client):
        await_(locmem_cache.async_clear())

        with client.websocket_connect("/ws/test_websocket_infinite_periodic") as websocket:
            websocket.send_json({"request_type": "x"})
            websocket.send_json({"request_type": "y"})

            response_pool = []
            for i in range(10):
                response = websocket.receive_json()
                response_pool.append(response["response"])

            xs = [resp for resp in response_pool if resp.startswith("x_")]
            ys = [resp for resp in response_pool if resp.startswith("y_")]
            assert len(xs) >= 3
            assert len(ys) >= 3

            websocket.close(1001)

        time.sleep(1)
        cache_keys = await_(locmem_cache.async_keys("*"))
        assert len(cache_keys) == 2
        results = await_(locmem_cache.async_get_many(cache_keys))
        assert set([value for key, value in results.items()]) == {"finished"}
