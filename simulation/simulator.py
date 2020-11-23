#!/usr/bin/env python3
from __future__ import annotations

import random
import heapq
from typing import List

from simulation.agent import *
from simulation.capability import *
from simulation.eviction_strategy import *
from simulation.events import *
from simulation.metrics import Metrics
from simulation.utility_targets import UtilityTargets


class Simulator:
    def __init__(self, seed: int, agents: List[Agent], escls, duration: float, utility_targets: UtilityTargets):
        # Initialise the PRNG and record the seed
        self.seed = seed
        self.rng = random.Random(self.seed)

        self.agents = agents
        for agent in self.agents:
            agent.sim = self

        self.es = escls(self)

        self.duration = duration
        self.utility_targets = utility_targets

        self.current_time = 0
        self.queue = []

        self.metrics = Metrics()

    def add_event(self, event):
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
        print(f"{self.current_time}|{message}")
