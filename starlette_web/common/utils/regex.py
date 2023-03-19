import fnmatch
import re


def redis_pattern_to_re_pattern(pattern: str) -> re.Pattern:
    """
    A helper function to match redis key pattern with re built-in module,
    Redis key pattern has different semantics, than regex.
    Official docs for redis key matching https://redis.io/commands/keys/

    Source: https://github.com/jamesls/fakeredis/pull/184/files#diff-abc1f5739597cb0cca80af31f32bc494b8d994472058fafdc57dba7ca4a8732dR242  # flake8: noqa

    >>> import re
    >>> from starlette_web.common.utils.regex import redis_pattern_to_re_pattern

    >>> redis_pattern = "keys:*"
    >>> re_pattern = redis_pattern_to_re_pattern(redis_pattern)
    >>> re_pattern
    [0] re.compile('keys:.*')
    >>> re.fullmatch(re_pattern, "keys:1")
    [1] <re.Match object; span=(0, 6), match='keys:1'>
    >>> re.fullmatch(re_pattern, "key:1")
    [2] None
    """
    parts = ['^']
    i = 0
    L = len(pattern)
    while i < L:
        c = pattern[i]
        if c == '?':
            parts.append('.')
        elif c == '*':
            parts.append('.*')
        elif c == '\\':
            if i < L - 1:
                i += 1
            parts.append(re.escape(pattern[i]))
        elif c == '[':
            parts.append('[')
            i += 1
            if i < L and pattern[i] == '^':
                i += 1
                parts.append('^')
            while i < L:
                if pattern[i] == '\\':
                    i += 1
                    if i < L:
                        parts.append(re.escape(pattern[i]))
                elif pattern[i] == ']':
                    break
                elif i + 2 <= L and pattern[i + 1] == '-':
                    start = pattern[i]
                    end = pattern[i + 2]
                    if start > end:
                        start, end = end, start
                    parts.append(re.escape(start) + '-' + re.escape(end))
                    i += 2
                else:
                    parts.append(re.escape(pattern[i]))
                i += 1
            parts.append(']')
        else:
            parts.append(re.escape(pattern[i]))
        i += 1
    parts.append('\\Z')
    regex = ''.join(parts)
    return re.compile(regex, re.S)
