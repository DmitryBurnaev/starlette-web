# Copied from https://github.com/django/django/blob/main/django/core/serializers/json.py

import json
import decimal
import datetime
import uuid


def _get_duration_components(duration):
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds = seconds % 60

    hours = minutes // 60
    minutes = minutes % 60

    return days, hours, minutes, seconds, microseconds


def _duration_iso_string(duration):
    if duration < datetime.timedelta(0):
        sign = '-'
        duration *= -1
    else:
        sign = ''

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = '.{:06d}'.format(microseconds) if microseconds else ""
    return '{}P{}DT{:02d}H{:02d}M{:02d}{}S'.format(sign, days, hours, minutes, seconds, ms)


class StarletteJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and UUIDs.

    >>> import json
    >>> import datetime
    >>> from decimal import Decimal
    >>> from starlette_web.common.utils.json import StarletteJSONEncoder
    >>> obj = {'key_decimal': Decimal('10.02'), 'key_timedelta': datetime.timedelta(days=1, seconds=13876)}  ## noqa E501
    >>> obj = {**obj, 'key_time': datetime.time(13,3,6,999), "key_date": datetime.date(2020,1,1)}
    >>> json.dumps(obj, cls=StarletteJSONEncoder)
    [0] '{"key_decimal": "10.02", "key_timedelta": "P1DT03H51M16S", "key_time": "13:03:06.000", "key_date": "2020-01-01"}'  ## noqa E501
    """
    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            return o.isoformat()
        elif isinstance(o, datetime.timedelta):
            return _duration_iso_string(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        else:
            return super().default(o)
