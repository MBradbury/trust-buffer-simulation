from __future__ import annotations

import random
import heapq

from simulation.agent import Agent
from simulation.events import BaseEvent, AgentInit
from simulation.metrics import Metrics
from simulation.utility_targets import UtilityTargets
from simulation.eviction_strategy import EvictionStrategy

class Simulator:
    def __init__(self,
                 seed: int,
                 agents: list[Agent],
                 escls: type[EvictionStrategy],
                 duration: float,
                 utility_targets: UtilityTargets,
                 log_level: int):
        # Initialise the PRNG and record the seed
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.agents = agents
        for agent in self.agents:
            agent.set_sim(self)

        self.es = escls(self)

        self.duration = duration
        self.utility_targets = utility_targets

        self.current_time: float = 0
        self.queue: list[BaseEvent] = []

        self.metrics = Metrics()
        self.metrics.duration = duration

        self.log_level = log_level

    def add_event(self, event: BaseEvent):
        heapq.heappush(self.queue, event)

    def run(self, max_start_delay: float):
        # Add start event
        for agent in self.agents:
            self.add_event(AgentInit(self.rng.uniform(0, max_start_delay), agent))

        while self.queue:
            item = heapq.heappop(self.queue)

            assert item.event_time >= self.current_time

            # Has the simulation finished?
            if item.event_time > self.duration:
                break

            self.current_time = item.event_time

            item.action(self)

    def log(self, message: str):
        if self.log_level > 0:
            print(f"{self.current_time}|{message}")
