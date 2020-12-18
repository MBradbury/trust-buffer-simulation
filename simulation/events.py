from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering

from simulation.constants import EPSILON
from simulation.capability_behaviour import InteractionObservation
from simulation.utility_targets import UtilityTargets

@total_ordering
@dataclass(eq=False)
class BaseEvent:
    event_time: float

    def log(self, sim: Simulation, message: str):
        sim.log(f"event|{self!r}|{message}")

    def action(self, sim: Simulation):
        self.log(sim, "performed")

    def __eq__(self, other: BaseEvent):
        return self.event_time == other.event_time

    def __lt__(self, other: BaseEvent):
        return self.event_time < other.event_time

class AgentInit(BaseEvent):
    def __init__(self, event_time: float, agent: Agent):
        super().__init__(event_time)
        self.agent = agent

    def action(self, sim: Simulation):
        super().action(sim)

        sim.add_event(AgentTrustDissemination(self.event_time + self.agent.next_trust_dissemination_period(sim.rng), self.agent))

        for capability in self.agent.capabilities:
            sim.add_event(AgentCapabilityTask(self.event_time + capability.next_task_period(sim.rng), self.agent, capability))

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s})"

class AgentCapabilityTask(BaseEvent):
    def __init__(self, event_time: float, agent: Agent, capability: Capability):
        super().__init__(event_time)
        self.agent = agent
        self.capability = capability

    def action(self, sim: Simulation):
        super().action(sim)

        sim.metrics.add_interaction_performed(self.event_time, self.agent, self.capability)

        selected_agent = self.agent.choose_agent_for_task(self.capability)

        if selected_agent is not None:
            self.agent.perform_interaction(selected_agent, self.capability)
        else:
            self.log(sim, "Unable to select agent to perform task")

        # Re-add this event
        sim.add_event(AgentCapabilityTask(self.event_time + self.capability.next_task_period(sim.rng), self.agent, self.capability))

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s}, {self.capability!s})"

class AgentTaskInteraction(BaseEvent):
    def __init__(self, event_time: float, source: Agent, capability: Capability, target: Agent, buffers: AgentBuffers):
        super().__init__(event_time)
        self.source = source
        self.capability = capability
        self.target = target
        self.buffers = buffers

    def _ensure_crypto_exists(self, sim: Simulation, agent: Agent, other: Agent):
        crypto = agent.buffers.find_crypto(other)
        if crypto is None:
            agent.receive_crypto_information(other)
            crypto = agent.buffers.find_crypto(other)
        if crypto is not None:
            sim.es.use_crypto(crypto)
        return crypto is not None

    def action(self, sim: Simulation):
        super().action(sim)

        # Source needs target's crypto information to process response
        our_crypto = self._ensure_crypto_exists(sim, self.source, self.target)
        assert our_crypto

        # Target also needs sources's crypto information to process response
        their_crypto = self._ensure_crypto_exists(sim, self.target, self.source)

        # Want to use the same seed for the interaction that does occur and the potential interactions
        seed = sim.rng.getrandbits(32)

        # Did the target perform the interaction well?
        outcome = self.target.capability_behaviour[self.capability].next_interaction(seed, sim.current_time)

        # Override interaction result if the target doesn't have our keys
        if not their_crypto:
            outcome = InteractionObservation.Incorrect

        # How would the other capabilities have performed?
        outcomes = {
            agent: agent.capability_behaviour[self.capability].peek_interaction(seed) if agent is not self.target else outcome
            for agent in sim.agents
            if agent is not self.source
        }
        self.log(sim, f"Outcomes|{outcomes}")

        # Who are we interested in evaluating the utility of the buffers for?
        if sim.utility_targets == UtilityTargets.All:
            utility_targets = outcomes.keys()
        elif sim.utility_targets == UtilityTargets.Good:
            utility_targets = [a for (a, o) in outcomes.items() if o == InteractionObservation.Correct]
        else:
            raise NotImplementedError()

        utility = self.buffers.utility(self.source, self.capability, targets=utility_targets)
        max_utility = self.buffers.max_utility(self.source, self.capability, targets=utility_targets)
        self.log(sim, f"Value of buffers {utility} (max={max_utility}) {self.capability}")

        sim.metrics.add_buffer_evaluation(sim.current_time, self.source, self.capability, outcomes,
                                          self.buffers.basic(), utility, max_utility, self.target, outcome)

        # Update source's interaction history
        self.source.update_trust_history(self.target, self.capability, outcome)

    def __repr__(self):
        return f"{type(self).__name__}(src={self.source!s}, cap={self.capability!s}, target={self.target!s})"

class AgentTrustDissemination(BaseEvent):
    def __init__(self, event_time: float, agent: Agent):
        super().__init__(event_time)
        self.agent = agent

    def action(self, sim: Simulation):
        super().action(sim)

        # Process trust reception at other agents
        for agent in sim.agents:
            if agent is not self.agent:
                agent.receive_trust_information(self.agent)

        # Re-add this event
        sim.add_event(AgentTrustDissemination(self.event_time + self.agent.next_trust_dissemination_period(sim.rng), self.agent))

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s})"

class AgentCryptoRequest(BaseEvent):
    def __init__(self, event_time: float, requester: Agent, agent: Agent):
        super().__init__(event_time)
        self.requester = requester
        self.agent = agent

    def action(self, sim: Simulation):
        super().action(sim)

        self.requester.receive_crypto_information(self.agent)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s}, of={self.agent!s})"

class AgentStereotypeRequest(BaseEvent):
    def __init__(self, event_time: float, requester: Agent, agent: Agent):
        super().__init__(event_time)
        self.requester = requester
        self.agent = agent

    def action(self, sim: Simulation):
        super().action(sim)

        for capability in self.agent.capabilities:
            self.requester.receive_stereotype_information(self.agent, capability)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s}, of={self.agent!s})"
