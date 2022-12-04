from __future__ import annotations

from enum import Enum
from typing import Optional


class Environment(str, Enum):
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

    def get_higher_environment(self) -> Optional[Environment]:
        if self == self.TEST:
            return self.STAGING

        if self == self.STAGING:
            return self.PRODUCTION

        return None
