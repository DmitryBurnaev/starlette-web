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

    re_pattern = redis_pattern_to_re_pattern("h[a-b]llo")
    assert re.fullmatch(re_pattern, "hallo")
    assert re.fullmatch(re_pattern, "hbllo")
    assert re.fullmatch(re_pattern, "hello") is None


def test_invalid_patterns():
    with pytest.raises(RuntimeError, match=re.escape("Nested sets in pattern not allowed.")):
        redis_pattern_to_re_pattern("keys:[[*]]")

    with pytest.raises(
        RuntimeError, match=re.escape("Orphan backslash in the end of the pattern.")
    ):
        redis_pattern_to_re_pattern("keys:[*]\\")

    with pytest.raises(
        RuntimeError, match=re.escape("Orphan closing bracket ] in pattern not allowed.")
    ):
        redis_pattern_to_re_pattern("keys:[*]]")

    with pytest.raises(
        RuntimeError,
        match=re.escape("Subpattern [^?] is only allowed to exclude a single character."),
    ):
        redis_pattern_to_re_pattern("keys:[^ab]")

    with pytest.raises(
        RuntimeError, match=re.escape("Hyphen outside [] block must be preceeded with backslash.")
    ):
        redis_pattern_to_re_pattern("keys:-a")
