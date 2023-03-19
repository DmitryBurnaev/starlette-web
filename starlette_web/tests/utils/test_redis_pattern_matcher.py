import re
import pytest

from starlette_web.common.utils.regex import redis_pattern_to_re_pattern


def test_redis_pattern_matcher():
    re_pattern = redis_pattern_to_re_pattern("keys:*")
    assert re.fullmatch(re_pattern, "keys:")
    assert re.fullmatch(re_pattern, "keys:1")
    assert re.fullmatch(re_pattern, "keys:abcde")
    assert re.fullmatch(re_pattern, "key:abcde") is None

    re_pattern = redis_pattern_to_re_pattern("keys:??")
    assert re.fullmatch(re_pattern, "keys:\\\\")
    assert re.fullmatch(re_pattern, "keys:3a")
    assert re.fullmatch(re_pattern, "keys:??")
    assert re.fullmatch(re_pattern, "keys:3aa") is None

    re_pattern = redis_pattern_to_re_pattern("h[^e]llo")
    assert re.fullmatch(re_pattern, "hello") is None
    assert re.fullmatch(re_pattern, "hallo")
    assert re.fullmatch(re_pattern, "hxllo")

    re_pattern = redis_pattern_to_re_pattern("h[^e-z]llo")
    assert re.fullmatch(re_pattern, "hello") is None
    assert re.fullmatch(re_pattern, "hzllo") is None
    assert re.fullmatch(re_pattern, "hallo")
    assert re.fullmatch(re_pattern, "hAllo")

    re_pattern = redis_pattern_to_re_pattern("h[a-b]llo")
    assert re.fullmatch(re_pattern, "hallo")
    assert re.fullmatch(re_pattern, "hbllo")
    assert re.fullmatch(re_pattern, "hello") is None


def test_invalid_patterns():
    with pytest.raises(re.error):
        redis_pattern_to_re_pattern("[")
