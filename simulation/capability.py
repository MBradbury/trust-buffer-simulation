from __future__ import annotations

class Capability:
    def __init__(self, name: str, task_period: float, priority: int):
        self.name = name
        self.task_period = task_period
        self.priority = priority

    def next_task_period(self, rng: random.Random) -> float:
        return rng.expovariate(1.0 / self.task_period)

    def __repr__(self):
        return f"Capability({self.name})"

    def __str__(self):
        return self.name

    # Can't allow this to be copied
    def __deepcopy__(self, memo):
        return self

    # Can't allow this to be copied
    def __copy__(self):
        return self
