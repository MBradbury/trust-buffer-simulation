from __future__ import annotations

from simulation.agent import Agent
from simulation.capability import Capability
from simulation.capability_behaviour import InteractionObservation

import bz2
from itertools import chain
from dataclasses import dataclass
import pickle

@dataclass
class BufferEvaluation:
    t: float
    source: str
    capability: str
    outcomes: dict
    buffers: dict
    utility: float
    max_utility: float
    target: str
    outcome: InteractionObservation

class Metrics:
    def __init__(self):
        self.interaction_performed = []
        self.buffers = []

        self.evicted_crypto = []
        self.evicted_trust = []
        self.evicted_reputation = []
        self.evicted_stereotype = []

    def add_buffer_evaluation(self, t: float,
                              source: Agent, capability: Capability,
                              outcomes: dict, buffers,
                              utility: float, max_utility: float,
                              target: Agent, outcome: InteractionObservation):
        pickleable_outcomes = {agent.name: outcome for (agent, outcome) in outcomes.items()}

        self.buffers.append(BufferEvaluation(t, source.name, capability.name, pickleable_outcomes, buffers, utility, max_utility, target.name, outcome))

    def add_evicted_crypto(self, t: float, agent: Agent, choice):
        self.evicted_crypto.append((t, agent.name, choice.basic()))
    def add_evicted_trust(self, t: float, agent: Agent, choice):
        self.evicted_trust.append((t, agent.name, choice.basic()))
    def add_evicted_reputation(self, t: float, agent: Agent, choice):
        self.evicted_reputation.append((t, agent.name, choice.basic()))
    def add_evicted_stereotype(self, t: float, agent: Agent, choice):
        self.evicted_stereotype.append((t, agent.name, choice.basic()))

    def add_interaction_performed(self, t: float, agent: Agent, capability: Capability):
        self.interaction_performed.append((t, agent.name, capability.name))

    def save(self, sim, args, path_prefix: str="./"):
        # Save information from sim

        self.args = args

        self.agent_names = list(sorted([agent.name for agent in sim.agents]))
        self.capability_names = list(sorted(set(chain.from_iterable(
            [capability.name for capability in agent.capabilities]
            for agent in sim.agents
        ))))

        self.behaviour_changes = {
            (agent.name, capability.name): behaviour.state_history
            for agent in sim.agents
            for (capability, behaviour) in agent.capability_behaviour.items()
        }

        with bz2.open(f"{path_prefix}metrics.{sim.seed}.pickle.bz2", "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def num_agents(self) -> int:
        return sum(num_agents for (num_agents, behaviour) in self.args.agents)

    def num_capabilities(self) -> int:
        return self.args.num_capabilities
