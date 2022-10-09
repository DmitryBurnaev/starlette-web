import datetime
import uuid

import pytest

from starlette_web.common.http.exceptions import BaseApplicationError
from starlette_web.tests.helpers import await_


def test_constance_get_value(config):
    test_constant_1_value = await_(config.get("TEST_CONSTANT_1"))
    assert test_constant_1_value == 1

    all_values = await_(config.mget(["TEST_CONSTANT_1", "TEST_CONSTANT_2"]))
    assert all_values == {"TEST_CONSTANT_1": 1, "TEST_CONSTANT_2": 2}


def test_constance_set_value(config):
    new_value = uuid.uuid4()
    await_(config.set("TEST_CONSTANT_UUID", new_value))
    test_constant_uuid = await_(config.get("TEST_CONSTANT_UUID"))
    assert new_value == test_constant_uuid


def test_constance_errors(config):
    new_value = uuid.uuid4()
    with pytest.raises(BaseApplicationError):
        await_(config.set("TEST_CONSTANT_DATETIME", new_value))
    test_constant_datetime = await_(config.get("TEST_CONSTANT_DATETIME"))
    assert type(test_constant_datetime) == datetime.datetime

    with pytest.raises(BaseApplicationError):
        await_(config.get("TEST_CONSTANT_NOT_EXISTING_KEY"))
