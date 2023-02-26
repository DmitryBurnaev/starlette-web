import re


def redis_pattern_to_re_pattern(pattern: str) -> re.Pattern:
    # Official docs for redis key-matching https://redis.io/commands/keys/
    while "**" in pattern:
        pattern = pattern.replace("**", "*")

    if not pattern:
        raise RuntimeError("Pattern is empty.")

    re_pattern = []
    in_braces = False
    prev_char_was_reverse_slash = False

    for i in range(len(pattern)):
        char = pattern[i]
        if prev_char_was_reverse_slash:
            prev_char_was_reverse_slash = False
            re_pattern.append(char)
        elif char != "\\":
            if char == "-" and not in_braces:
                raise RuntimeError("Hyphen outside [] block must be preceeded with backslash.")
            elif char == "[":
                if in_braces:
                    raise RuntimeError("Nested sets in pattern not allowed.")
                in_braces = True
            elif char == "]":
                if not in_braces:
                    raise RuntimeError("Orphan closing bracket ] in pattern not allowed.")
                in_braces = False
            elif char == "^" and in_braces:
                try:
                    assert pattern[i + 2] == "]"
                except (IndexError, AssertionError):
                    raise RuntimeError(
                        "Subpattern [^?] is only allowed to exclude a single character."
                    )
            elif char in "?*" and not in_braces:
                re_pattern.append(".")

            re_pattern.append(char)
        else:
            prev_char_was_reverse_slash = True

    if prev_char_was_reverse_slash:
        raise RuntimeError("Orphan backslash in the end of the pattern.")

    return re.compile("".join(re_pattern))
