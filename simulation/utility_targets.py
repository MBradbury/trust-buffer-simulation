from enum import Enum

class UtilityTargets(Enum):
    All = "all"
    Good = "good"

    def __str__(self):
        return self.value
