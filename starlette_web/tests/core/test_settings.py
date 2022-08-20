import pytest

from starlette_web.common.conf import settings
from starlette_web.common.http.exceptions import ImproperlyConfigured


def test_settings():
    value = settings.APPLICATION_CLASS
    assert value == "starlette_web.tests.app.TestStarletteApplication"

    with pytest.raises(ImproperlyConfigured) as err:
        _ = settings.INEXISTENT_SETTING

    assert err.value.details == "Setting INEXISTENT_SETTING is not configured."
    assert err.value.message == "Application is configured improperly."
