from starlette_web.common.caches import caches
from starlette_web.tests.core.helpers.base_cache_tester import BaseCacheTester


class TestFileCache(BaseCacheTester):
    def test_file_cache_base_ops(self):
        self._run_base_cache_test(caches["files"])

    def test_file_cache_many_ops(self):
        self._run_cache_many_ops_test(caches["files"])

    def test_file_lock(self):
        self._run_cache_lock_test(caches["files"])

    def test_file_lock_race_condition(self):
        self._run_cache_mutual_lock_test(caches["files"])

    def test_file_lock_correct_task_blocking(self):
        self._run_cache_timeouts_test(caches["files"])
