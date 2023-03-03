from typing import List


class BaseAppConfig:
    app_name: str
    app_requirements: List[str] = []

    def initialize(self):
        pass

    def perform_checks(self):
        pass
