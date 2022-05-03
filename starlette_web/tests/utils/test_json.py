import json
import datetime
from decimal import Decimal

from starlette_web.common.utils import StarletteJSONEncoder


def test_starlette_json_encoder():
    obj = {
        "key_decimal": Decimal("10.02"),
        "key_timedelta": datetime.timedelta(days=1, seconds=13876),
        "key_time": datetime.time(13, 3, 6, 999),
        "key_date": datetime.date(2020, 1, 1),
        "key_string": "string",
        "key_list": [{"key": "inside_object"}],
    }

    result = (
        '{"key_decimal": "10.02", "key_timedelta": "P1DT03H51M16S", "key_time": "13:03:06.000999", '
        '"key_date": "2020-01-01", "key_string": "string", "key_list": [{"key": "inside_object"}]}'
    )

    assert json.dumps(obj, cls=StarletteJSONEncoder) == result
