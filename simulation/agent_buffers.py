from __future__ import annotations

import copy
from dataclasses import dataclass

from simulation.bounded_list import BoundExceedError, BoundedList
from simulation.capability import *

@dataclass
class CryptoItem:
    agent: Agent

    eviction_data: Any = None

    def basic(self):
        return (self.agent.name,)

@dataclass
class TrustItem:
    agent: Agent
    capability: Capability

    correct_count: int = 0
    incorrect_count: int = 0

    eviction_data: Any = None

    def record(self, outcome: str):
        if outcome == InteractionObservation.Correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1

    def total_count(self) -> int:
        return self.correct_count + self.incorrect_count

    def brs_trust(self) -> float:
        if self.total_count() == 0:
            # Avoid division by zero errors
            return 0.5
        else: 
            return self.correct_count / float(self.correct_count + self.incorrect_count)

    def basic(self):
        return (self.agent.name, self.capability.name)


@dataclass(repr=False)
class ReputationItem:
    agent: Agent
    trust_items: List[TrustItem]

    eviction_data: Any = None

    def __str__(self):
        return f"ReputationItem(agent={self.agent}, trust_items=..., eviction_data={self.eviction_data})"

    def basic(self):
        return (self.agent.name, [trust_item.basic() for trust_item in self.trust_items])

@dataclass
class StereotypeItem:
    agent: Agent
    capability: Capability

    eviction_data: Any = None

    def basic(self):
        return (self.agent.name, self.capability.name)

class AgentBuffers:
    buffers = ("crypto", "trust", "reputation", "stereotype")

    def __init__(self, agent: Agent, crypto_bux_max: int, trust_bux_max: int, reputation_bux_max: int, stereotype_bux_max: int):
        self.agent = agent

        self.crypto = BoundedList(length=crypto_bux_max)
        self.trust = BoundedList(length=trust_bux_max)
        self.reputation = BoundedList(length=reputation_bux_max)
        self.stereotype = BoundedList(length=stereotype_bux_max)

    def frozen(self) -> AgentBuffers:
        f = AgentBuffers(self.agent, self.crypto.length, self.trust.length, self.reputation.length, self.stereotype.length)

        for b in self.buffers:
            getattr(f, b).extend([copy.copy(i) for i in getattr(self, b)])
            getattr(f, b).freeze()

        return f

    def basic(self) -> dict:
        return {
            b: [x.basic() for x in getattr(self, b)]
            for b in self.buffers
        }

    def find_crypto(self, agent: Agent) -> CryptoItem:
        for item in self.crypto:
            if item.agent is agent:
                return item

        return None

    def find_trust(self, agent: Agent, capability: Capability) -> TrustItem:
        for item in self.trust:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def find_trust_by_agent(self, agent: Agent) -> List[TrustItem]:
        result = []

        for item in self.trust:
            if item.agent is agent:
                result.append(item)

        return result

    def find_reputation(self, agent: Agent) -> ReputationItem:
        for item in self.reputation:
            if item.agent is agent:
                return item

        return None

    def find_reputation_contents_by_agent(self, agent: Agent) -> List[ReputationItem]:
        result = []

        for item in self.reputation:
            if any(trust_item.agent is agent for trust_item in item.trust_items):
                result.append(item)

        return result

    def find_reputation_contents(self, agent: Agent, capability: Capability) -> List[ReputationItem]:
        result = []

        for item in self.reputation:
            if any(trust_item.agent is agent and trust_item.capability is capability for trust_item in item.trust_items):
                result.append(item)

        return result

    def find_stereotype(self, agent: Agent, capability: Capability) -> StereotypeItem:
        for item in self.stereotype:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def find_stereotype_by_agent(self, agent: Agent) -> List[StereotypeItem]:
        result = []

        for item in self.stereotype:
            if item.agent is agent:
                result.append(item)

        return result

    def buffer_has_agent_count(self, agent: Agent, buffers="CTRS") -> int:
        result = 0

        if "C" in buffers:
            if self.find_crypto(agent):
                result += 1

        if "T" in buffers:
            if self.find_trust_by_agent(agent):
                result += 1

        if "R" in buffers:
            if self.find_reputation_contents_by_agent(agent):
                result += 1

        if "S" in buffers:
            if self.find_stereotype_by_agent(agent):
                result += 1

        return result

    def buffer_has_agent_capability_count(self, agent: Agent, capability: Capability, buffers="CTRS") -> int:
        result = 0

        if "C" in buffers:
            if self.find_crypto(agent):
                result += 1

        if "T" in buffers:
            if self.find_trust(agent, capability):
                result += 1

        if "R" in buffers:
            if self.find_reputation_contents(agent, capability):
                result += 1

        if "S" in buffers:
            if self.find_stereotype(agent, capability):
                result += 1

        return result


    def add_crypto(self, es: EvictionStrategy, item: CryptoItem):
        try:
            self.crypto.append(item)
        except BoundExceedError:
            # Consider evicting
            choice = es.choose_crypto(self.crypto, self, item)
            if choice is not None:
                self.crypto.remove(choice)
                self.log(f"Evicted {choice} from {[x.basic() for x in self.crypto]}")
                self.agent.sim.metrics.add_evicted_crypto(self.agent.sim.current_time, self.agent, choice)

                self.crypto.append(item)
            else:
                return

        es.add_crypto(item)

    def add_trust(self, es: EvictionStrategy, item: TrustItem):
        try:
            self.trust.append(item)
        except BoundExceedError:
            choice = es.choose_trust(self.trust, self, item)
            if choice is not None:
                self.trust.remove(choice)
                self.log(f"Evicted {choice} from {[x.basic() for x in self.trust]}")
                self.agent.sim.metrics.add_evicted_trust(self.agent.sim.current_time, self.agent, choice)

                self.trust.append(item)
            else:
                return

        es.add_trust(item)

    def add_reputation(self, es: EvictionStrategy, item: ReputationItem):
        try:
            self.reputation.append(item)
        except BoundExceedError:
            choice = es.choose_reputation(self.reputation, self, item)
            if choice is not None:
                self.reputation.remove(choice)
                self.log(f"Evicted {choice} from {[x.basic() for x in self.reputation]}")
                self.agent.sim.metrics.add_evicted_reputation(self.agent.sim.current_time, self.agent, choice)

                self.reputation.append(item)
            else:
                return

        es.add_reputation(item)

    def add_stereotype(self, es: EvictionStrategy, item: StereotypeItem):
        try:
            self.stereotype.append(item)
        except BoundExceedError:
            choice = es.choose_stereotype(self.stereotype, self, item)
            if choice is not None:
                self.stereotype.remove(choice)
                self.log(f"Evicted {choice} from {[x.basic() for x in self.stereotype]}")
                self.agent.sim.metrics.add_evicted_stereotype(self.agent.sim.current_time, self.agent, choice)

                self.stereotype.append(item)
            else:
                return

        es.add_stereotype(item)

    def utility(self, agent: Agent, capability: Capability, targets: List=None):
        sim = agent.sim

        def Uc(other: Agent):
            return 1 if self.find_crypto(other) is not None else 0

        def Ud(other: Agent):
            item = self.find_trust(other, capability)
            if item is None:
                return 0
            return 1 if item.total_count() > 0 else 0

        def Up(other: Agent):
            items = self.find_reputation_contents(other, capability)
            for item in items:
                if any(trust_item.total_count() > 0 for trust_item in item.trust_items):
                    return 1
            return 0

        def Us(other: Agent):
            item = self.find_stereotype(other, capability)
            if item is None:
                return 0
            return 1

        if targets is None:
            targets = sim.agents

        agents = [
            a for a in targets
            if a is not agent and capability in a.capabilities
        ]

        #self.log(f"#Evaluating utility for {agent}:")
        #for a in agents:
        #    self.log(f"#\t{a}: Uc={Uc(a)} Ud={Ud(a)} Up={Up(a)} Us={Us(a)}")

        if not agents:
            return float("NaN")
        else:
            return sum(Uc(a) * (1 + Ud(a) + Up(a) + Us(a)) * (1.0/4.0) for a in agents) / len(agents)

    def max_utility(self, agent: Agent, capability: Capability, targets: List=None):
        sim = agent.sim

        if targets is None:
            targets = sim.agents

        agents = [
            a for a in targets
            if a is not agent and capability in a.capabilities
        ]

        if not agents:
            return float("NaN")

        selected_agents = agents[0:min(self.crypto.length, len(agents))]
        selected_trust = selected_agents[0:min(self.trust.length, len(selected_agents))]
        selected_stereotype = selected_agents[0:min(self.stereotype.length, len(selected_agents))]
        selected_reputation = selected_agents[0:min(self.reputation.length, len(selected_agents))]

        # crypto and reputation per agent
        # trust and stereotype per (agent, capability)

        def U(other: Agent) -> int:
            result = 0

            if other in selected_agents:
                result += 1
            else:
                return 0

            if other in selected_trust:
                result += 1

            if other in selected_stereotype:
                result += 1

            if other in selected_reputation:
                result += 1

            return result

        return sum(U(a) / 4.0 for a in agents) / len(agents)

    def log(self, message: str):
        self.agent.log(message)
