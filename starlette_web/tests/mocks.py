import asyncio
import multiprocessing
from unittest.mock import Mock


class BaseMock:
    """Base class for class mocking

    # users class
    >>> class Vehicle:
    >>>    def run(self): ...

    # mock class
    >>> class MockVehicle(BaseMock):
    >>>     target_class = Vehicle
    >>>     def __init__(self):
    >>>         self.run = Mock(return_value=None)  # noqa

    """

    CODE_OK = 0
    target_obj = None

    @property
    def target_class(self):
        raise NotImplementedError

    def get_mocks(self):
        return [attr for attr, val in self.__dict__.items() if callable(val)]

    def mock_init(self, *args, **kwargs):
        ...

    @staticmethod
    def async_return(result):
        f = asyncio.Future()
        f.set_result(result)
        return f


class MockProcess(BaseMock):
    target_class = multiprocessing.context.Process

    def __init__(self):
        self.start = Mock(return_value=None)
        self.terminate = Mock(return_value=None)
        self.__repr__ = Mock(return_value="TestProcess")
