from __future__ import annotations

import copy
from dataclasses import dataclass
from itertools import chain

from simulation.bounded_list import BoundExceedError, BoundedList

from simulation.capability import *
from simulation.events import *
from simulation.constants import EPSILON

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
        return (self.agent.name, self.capability.name, self.correct_count, self.incorrect_count)


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
    def __init__(self, agent: Agent, crypto_bux_max: int, trust_bux_max: int, reputation_bux_max: int, stereotype_bux_max: int):
        self.agent = agent

        self.crypto = BoundedList(length=crypto_bux_max)
        self.trust = BoundedList(length=trust_bux_max)
        self.reputation = BoundedList(length=reputation_bux_max)
        self.stereotype = BoundedList(length=stereotype_bux_max)

    def find_crypto(self, agent) -> CryptoItem:
        for item in self.crypto:
            if item.agent is agent:
                return item

        return None

    def find_trust(self, agent: Agent, capability: Capability) -> TrustItem:
        for item in self.trust:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def find_reputation(self, agent: Agent) -> ReputationItem:
        for item in self.reputation:
            if item.agent is agent:
                return item

        return None

    def find_stereotype(self, agent: Agent, capability: Capability) -> StereotypeItem:
        for item in self.stereotype:
            if item.agent is agent and item.capability is capability:
                return item

        return None

    def add_crypto(self, es: EvictionStrategy, item: CryptoItem):
        try:
            self.crypto.append(item)
        except BoundExceedError:
            # Consider evicting
            choice = es.choose_crypto(self.crypto, self)
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
            choice = es.choose_trust(self.trust, self)
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
            choice = es.choose_reputation(self.reputation, self)
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
            choice = es.choose_stereotype(self.stereotype, self)
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
            for agent_via in sim.agents:
                item = self.find_reputation(agent_via)
                if item is None:
                    continue

                for trust_item in item.trust_items:
                    if trust_item.total_count() > 0:
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

        print(f"#Evaluating utility for {agent}:")
        for a in agents:
            print(f"#\t{a}: Uc={Uc(a)} Ud={Ud(a)} Up={Up(a)} Us={Us(a)}")

        if not agents:
            return float("NaN")
        else:
            return sum(Uc(a) * (Ud(a) + Up(a) + Us(a)) * 1.0/3.0 for a in agents) / len(agents)

    def max_utility(self):
        sim = self.agent.sim

        agents = set(sim.agents) - {self.agent}
        sorted_agents = list(sorted(agents, key=lambda x: len(set(x.capabilities) & set(self.agent.capabilities)), reverse=True))
        selected_agents = sorted_agents[0:self.crypto.length]

        # crypto and reputation per agent
        # trust and stereotype per (agent, capability)

        global available_trust
        global available_reputation
        global available_stereotype

        available_trust = self.trust.length
        available_reputation = self.reputation.length
        available_stereotype = self.stereotype.length

        def Ud(other: Agent):
            global available_trust
            if available_trust > 0:
                available_trust -= 1
                return 1
            else:
                return 0

        def Up(other: Agent):
            global available_reputation
            if available_reputation > 0:
                available_reputation -= 1
                return 1
            else:
                return 0

        def Us(other: Agent):
            global available_stereotype
            if available_stereotype > 0:
                available_stereotype -= 1
                return 1
            else:
                return 0

        return sum((Ud(a) + Up(a) + Us(a)) * 1.0/3.0 for a in selected_agents) / len(agents)

    def log(self, message: str):
        self.agent.log(message)


class Agent:
    def __init__(self, name: str, capabilities: List[Capability], behaviour, trust_dissem_period: float,
                crypto_bux_max: int, trust_bux_max: int, reputation_bux_max: int, stereotype_bux_max: int):
        self.name = name
        self.capabilities = capabilities
        self.capability_behaviour = {capability: behaviour() for capability in self.capabilities}

        self.trust_dissem_period = trust_dissem_period

        self.buffers = AgentBuffers(self, crypto_bux_max, trust_bux_max, reputation_bux_max, stereotype_bux_max)

        self.sim = None

    def next_trust_dissemination_period(self, rng: random.Random) -> float:
        return rng.expovariate(1.0 / self.trust_dissem_period)

    def request_stereotype(self, agent: Agent):
        self.sim.add_event(AgentStereotypeRequest(self.sim.current_time + EPSILON, self, agent))

    def request_crypto(self, agent: Agent):
        self.sim.add_event(AgentCryptoRequest(self.sim.current_time + EPSILON, self, agent))

    def receive_trust_information(self, agent: Agent):
        if agent is self:
            return

        crypto_item = self.buffers.find_crypto(agent)
        if crypto_item is None:
            self.request_crypto(agent)
            return

        self.sim.es.use_crypto(crypto_item)

        # Need to request sterotype information here, if missing any
        if any(self.buffers.find_stereotype(agent, capability) is None for capability in self.capabilities):
            self.request_stereotype(agent)

        # Record reputation information
        reputation_item = self.buffers.find_reputation(agent)
        if reputation_item is None:
            # Try to add this new item
            new_reputation_item = ReputationItem(agent, copy.copy(agent.buffers.trust))

            self.buffers.add_reputation(self.sim.es, new_reputation_item)
        else:
            # Update the item
            reputation_item.trust_items = copy.copy(agent.buffers.trust)


    def receive_crypto_information(self, agent: Agent):
        if agent is self:
            return

        crypto_item = self.buffers.find_crypto(agent)
        if crypto_item is not None:
            return

        new_crypto_item = CryptoItem(agent)

        self.buffers.add_crypto(self.sim.es, new_crypto_item)

    def receive_stereotype_information(self, agent: Agent, capability: Capability):
        if agent is self:
            return

        # Don't want to record capabilities we do not have
        if capability not in self.capabilities:
            return

        stereotype_item = self.buffers.find_stereotype(agent, capability)
        if stereotype_item is not None:
            return

        new_stereotype_item = StereotypeItem(agent, capability)

        self.buffers.add_stereotype(self.sim.es, new_stereotype_item)

    def update_trust_history(self, agent: Agent, capability: Capability, outcome: InteractionObservation):
        trust_item = self.buffers.find_trust(agent, capability)

        if trust_item is None:
            new_trust_item = TrustItem(agent, capability)

            self.buffers.add_trust(self.sim.es, new_trust_item)

            trust_item = self.buffers.find_trust(agent, capability)
            assert trust_item is new_trust_item

        trust_item.record(outcome)

        self.log(f"Value of buffers after update {self.buffers.utility(self, capability, targets=[agent])} {capability}")

    def choose_agent_for_task(self, capability: Capability):
        try:
            item = self.sim.rng.choice([item for item in self.buffers.crypto if capability in item.agent.capabilities])

            self.sim.es.use_crypto(item)

            self.sim.es.use_trust(self.buffers.find_trust(item.agent, capability))

            for reputation_item in self.buffers.reputation:
                if any(trust_item.agent is item and trust_item.capability is capability for trust_item in reputation_item.trust_items):
                    self.sim.es.use_reputation(reputation_item)

            self.sim.es.use_stereotype(self.buffers.find_stereotype(item.agent, capability))

            return item.agent
        except IndexError:
            return None

    def perform_interaction(self, selected_agent: Agent, capability: Capability):
        # Record the values in the buffers at the time the interaction was initiated
        buffers = copy.copy(self.buffers)

        self.sim.add_event(AgentTaskInteraction(self.sim.current_time + EPSILON, self, capability, selected_agent, buffers))


    def log(self, message: str):
        self.sim.log(f"{self!s}|{message}")

    def __repr__(self):
        return f"Agent({self.name})"

    def __str__(self):
        return self.name
