import time

from starlette_web.common.caches import caches
from starlette_web.tests.helpers import await_


default_cache = caches['default']


def test_redis_cache():
    test_key = 'b6e58cf5-4b83-400c-8c11-1dee87174200'
    await_(default_cache.async_delete(test_key))

    value = await_(default_cache.async_get(test_key))
    assert value is None

    value_obj = {
        'item_1': None,
        'item_2': True,
        'item_3': 432534523452345234523452435,
        'item_4': ['str', 12, None, True, {}],
        'item_5': {
            'item_5_1': False,
            'item_5_2': 34,
        },
    }

    await_(default_cache.async_set(test_key, value_obj, 4))
    value = await_(default_cache.async_get(test_key))
    assert value == value_obj
    assert await_(default_cache.async_has_key(test_key))

    time.sleep(4)
    value = await_(default_cache.async_get(test_key))
    assert value is None


def test_redis_cache_many():
    test_key_1 = '2a8006ac-e296-486e-8044-b27517aaaaaa'
    test_key_2 = '2a8006ac-e296-486e-8044-b27517bbbbbb'

    await_(default_cache.async_delete_many([test_key_1, test_key_2]))

    keys = await_(default_cache.async_keys('2a8006ac-e296-486e-8044-b27517*'))
    assert len(keys) == 0

    await_(default_cache.async_set_many({
        test_key_1: 10,
        test_key_2: 42,
    }, timeout=2))

    keys = await_(default_cache.async_keys('2a8006ac-e296-486e-8044-b27517*'))
    assert len(keys) == 2

    values = await_(default_cache.async_get_many(keys))
    assert values == {
        test_key_1: 10,
        test_key_2: 42,
    }

    await_(default_cache.async_set(test_key_2, 10))
    time.sleep(3)

    keys = await_(default_cache.async_keys('2a8006ac-e296-486e-8044-b27517*'))
    assert len(keys) == 1
