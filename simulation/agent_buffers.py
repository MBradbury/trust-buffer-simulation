from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from simulation.bounded_list import BoundExceedError, BoundedList
from simulation.capability import Capability
from simulation.capability_behaviour import InteractionObservation

from cuckoopy import CuckooFilter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.agent import Agent
    from simulation.eviction_strategy import EvictionStrategy

@dataclass(slots=True)
class CryptoItem:
    agent: Agent

    eviction_data: Any = None

    def basic(self):
        return (self.agent.name,)

@dataclass(slots=True)
class TrustItem:
    agent: Agent
    capability: Capability

    correct_count: int = 0
    incorrect_count: int = 0

    eviction_data: Any = None

    def record(self, outcome: InteractionObservation):
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

@dataclass(repr=False, slots=True)
class ReputationItem:
    agent: Agent
    trust_items: BoundedList[TrustItem]

    eviction_data: Any = None

    def __str__(self):
        return f"ReputationItem(agent={self.agent}, trust_items=..., eviction_data={self.eviction_data})"

    def basic(self):
        return (self.agent.name, [trust_item.basic() for trust_item in self.trust_items])

@dataclass(slots=True)
class StereotypeItem:
    agent: Agent
    capability: Capability

    eviction_data: Any = None

    def basic(self):
        return (self.agent.name, self.capability.name)

@dataclass(slots=True)
class ChallengeResponseItem:
    agent: Agent

    good: bool
    epoch: int = 0
    sequential_fails: int = 0

    eviction_data: Any = None

    def basic(self):
        return (self.agent.name,)

    def record(self, outcome: InteractionObservation):
        old_good = self.good

        if outcome == InteractionObservation.Correct:
            self.good = True
        else:
            self.good = False

        # Increment epoch when changing goodness
        if old_good != self.good:
            self.epoch += 1

        # Update sequential fails
        if self.good:
            self.sequential_fails = 0
        else:
            self.sequential_fails += 1

class AgentBuffers:
    def __init__(self,
                 agent: Agent,
                 crypto_bux_max: int,
                 trust_bux_max: int,
                 reputation_bux_max: int,
                 stereotype_bux_max: int,
                 cr_buf_max: int,
                 cuckoo_max_capacity: int):
        self.agent = agent

        self.crypto = BoundedList[CryptoItem](length=crypto_bux_max)
        self.trust = BoundedList[TrustItem](length=trust_bux_max)
        self.reputation = BoundedList[ReputationItem](length=reputation_bux_max)
        self.stereotype = BoundedList[StereotypeItem](length=stereotype_bux_max)
        self.cr = BoundedList[ChallengeResponseItem](length=cr_buf_max)

        self.badlist = None
        self.encountered = None
        if cuckoo_max_capacity > 0:
            # Important to maintain this as a badlist
            # Cuckoo filters will provide the ability to test
            # 1. if an item is definitely not in the cuckoo filter
            # 2. if an item may be in the cuckoo filter
            # We are interested in absence from being bad,
            # so more important to be able to test if an item is not in the list for certain
            self.badlist = CuckooFilter(capacity=cuckoo_max_capacity, bucket_size=4, fingerprint_size=1)
            self.encountered = CuckooFilter(capacity=cuckoo_max_capacity, bucket_size=4, fingerprint_size=1)

    def frozen_copy(self) -> AgentBuffers:
        f = copy.deepcopy(self)
        f.crypto.freeze()
        f.trust.freeze()
        f.reputation.freeze()
        f.stereotype.freeze()
        f.cr.freeze()

        return f

    def basic(self) -> dict[str, list[tuple[Any, ...]]]:
        return {
            "crypto":       [x.basic() for x in self.crypto],
            "trust":        [x.basic() for x in self.trust],
            "reputation":   [x.basic() for x in self.reputation],
            "stereotype":   [x.basic() for x in self.stereotype],
            "cr":           [x.basic() for x in self.cr],
        }

    def find_crypto(self, agent: Agent) -> CryptoItem | None:
        for item in self.crypto:
            if item.agent is agent:
                return item

        return None

    def find_trust(self, agent: Agent, capability: Capability) -> TrustItem | None:
        for item in self.trust:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def find_trust_by_agent(self, agent: Agent) -> list[TrustItem]:
        result: list[TrustItem] = []

        for item in self.trust:
            if item.agent is agent:
                result.append(item)

        return result

    def find_reputation(self, agent: Agent) -> ReputationItem | None:
        for item in self.reputation:
            if item.agent is agent:
                return item

        return None

    def find_reputation_contents_by_agent(self, agent: Agent) -> list[ReputationItem]:
        result: list[ReputationItem] = []

        for item in self.reputation:
            if any(trust_item.agent is agent for trust_item in item.trust_items):
                result.append(item)

        return result

    def find_reputation_contents(self, agent: Agent, capability: Capability) -> list[ReputationItem]:
        result: list[ReputationItem] = []

        for item in self.reputation:
            if any(trust_item.agent is agent and trust_item.capability is capability for trust_item in item.trust_items):
                result.append(item)

        return result

    def find_stereotype(self, agent: Agent, capability: Capability) -> StereotypeItem | None:
        for item in self.stereotype:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def find_stereotype_by_agent(self, agent: Agent) -> list[StereotypeItem]:
        result: list[StereotypeItem] = []

        for item in self.stereotype:
            if item.agent is agent:
                result.append(item)

        return result

    def find_challenge_response(self, agent: Agent) -> ChallengeResponseItem | None:
        for item in self.cr:
            if item.agent is agent:
                return item

        return None

    def buffer_has_agent_count(self, agent: Agent, buffers: str="CTRSE") -> int:
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

        if "E" in buffers:
            if self.find_challenge_response(agent):
                result += 1

        return result

    def buffer_has_agent_capability_count(self, agent: Agent, capability: Capability, buffers: str="CTRSE") -> int:
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

        if "E" in buffers:
            if self.find_challenge_response(agent):
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
                assert self.agent.sim is not None
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
                assert self.agent.sim is not None
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
                assert self.agent.sim is not None
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
                assert self.agent.sim is not None
                self.agent.sim.metrics.add_evicted_stereotype(self.agent.sim.current_time, self.agent, choice)

                self.stereotype.append(item)
            else:
                return

        es.add_stereotype(item)

    def add_challenge_response(self, es: EvictionStrategy, item: ChallengeResponseItem):
        try:
            self.cr.append(item)
        except BoundExceedError:
            choice = es.choose_challenge_response(self.cr, self, item)
            if choice is not None:
                self.cr.remove(choice)
                self.log(f"Evicted {choice} from {[x.basic() for x in self.cr]}")
                assert self.agent.sim is not None
                self.agent.sim.metrics.add_evicted_challenge_response(self.agent.sim.current_time, self.agent, choice)

                self.cr.append(item)
            else:
                return

        es.add_challenge_response(item)

    def utility(self, agent: Agent, capability: Capability, targets: list[Agent] | None=None):
        sim = agent.sim
        assert sim is not None

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

    def max_utility(self, agent: Agent, capability: Capability, targets: list[Agent] | None=None):
        sim = agent.sim
        assert sim is not None

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
