def cut_string(source_string: str, max_length: int, finish_seq: str = "...") -> str:
    """
    Allows limiting source_string and append required sequence

    >>> cut_string('Some long string', max_length=13)
    'Some long ...'
    >>> cut_string('Some long string', max_length=8, finish_seq="***")
    'Some ***'
    >>> cut_string('Some long string', max_length=1)
    ''
    """
    if len(source_string) > max_length:
        slice_length = max_length - len(finish_seq)
        return source_string[:slice_length] + finish_seq if (slice_length > 0) else ""

    return source_string
