from __future__ import annotations

from functools import total_ordering

from simulation.capability_behaviour import InteractionObservation
from simulation.utility_targets import UtilityTargets
from simulation.constants import EPSILON

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.simulator import Simulator
    from simulation.agent import Agent
    from simulation.agent_buffers import AgentBuffers
    from simulation.capability import Capability

@total_ordering
class BaseEvent:
    def __init__(self, event_time: float):
        self.event_time = event_time

    def log(self, sim: Simulator, message: str):
        sim.log(f"event|{self!r}|{message}")

    def action(self, sim: Simulator):
        self.log(sim, "performed")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BaseEvent) and self.event_time == other.event_time

    def __lt__(self, other: BaseEvent):
        return self.event_time < other.event_time

class BaseCryptoEvent(BaseEvent):
    def _ensure_crypto_exists(self, sim: Simulator, agent: Agent, other: Agent) -> bool:
        crypto = agent.buffers.find_crypto(other)
        if crypto is None:
            agent.receive_crypto_information(other)
            crypto = agent.buffers.find_crypto(other)
        if crypto is not None:
            sim.es.use_crypto(crypto)
        return crypto is not None

class AgentInit(BaseEvent):
    def __init__(self, event_time: float, agent: Agent):
        super().__init__(event_time)
        self.agent = agent

    def action(self, sim: Simulator):
        super().action(sim)

        # Start trust dissemination if we are configured to store the information
        sim.add_event(AgentTrustDissemination(self.event_time + EPSILON, self.agent))

        for capability in self.agent.capabilities:
            sim.add_event(AgentCapabilityTask(self.event_time + capability.next_task_period(sim.rng), self.agent, capability))

        if self.agent.challenge_response_period is not None:
            sim.add_event(AgentSendChallenge(self.event_time + self.agent.challenge_response_period, self.agent))

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s})"

class AgentCapabilityTask(BaseEvent):
    def __init__(self, event_time: float, agent: Agent, capability: Capability):
        super().__init__(event_time)
        self.agent = agent
        self.capability = capability

    def action(self, sim: Simulator):
        super().action(sim)

        selected_agent = self.agent.choose_agent_for_task(self.capability)

        if selected_agent is not None:
            self.agent.perform_interaction(selected_agent, self.capability)
            sim.metrics.add_interaction_performed(self.event_time, self.agent, self.capability)
        else:
            self.log(sim, "Unable to select agent to perform task")
            sim.metrics.add_interaction_agent_select_fail(sim.current_time, self.agent, self.capability)

        # Re-add this event
        self.event_time += self.capability.next_task_period(sim.rng)
        sim.add_event(self)

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s}, {self.capability!s})"

class AgentTaskInteraction(BaseCryptoEvent):
    def __init__(self, event_time: float, source: Agent, capability: Capability, target: Agent, buffers: AgentBuffers):
        super().__init__(event_time)
        self.source = source
        self.capability = capability
        self.target = target
        self.buffers = buffers

    def action(self, sim: Simulator):
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
            utility_targets = list(outcomes.keys())
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

    def action(self, sim: Simulator):
        super().action(sim)

        # Process trust reception at other agents
        for agent in sim.agents:
            if agent is not self.agent:
                agent.receive_trust_information(self.agent)

        # Re-add this event
        self.event_time += self.agent.next_trust_dissemination_period(sim.rng)
        sim.add_event(self)

    def __repr__(self):
        return f"{type(self).__name__}({self.agent!s})"

class AgentCryptoRequest(BaseEvent):
    def __init__(self, event_time: float, requester: Agent, agent: Agent):
        super().__init__(event_time)
        self.requester = requester
        self.agent = agent

    def action(self, sim: Simulator):
        super().action(sim)

        self.requester.receive_crypto_information(self.agent)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s}, of={self.agent!s})"

class AgentStereotypeRequest(BaseEvent):
    def __init__(self, event_time: float, requester: Agent, agent: Agent):
        super().__init__(event_time)
        self.requester = requester
        self.agent = agent

    def action(self, sim: Simulator):
        super().action(sim)

        for capability in self.agent.capabilities:
            self.requester.receive_stereotype_information(self.agent, capability)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s}, of={self.agent!s})"

class AgentSendChallenge(BaseEvent):
    def __init__(self, event_time: float, requester: Agent):
        super().__init__(event_time)
        self.requester = requester

    def action(self, sim: Simulator):
        super().action(sim)
        assert self.requester.challenge_response_period is not None

        # Send challenge to everyone in crypto
        for crypto in self.requester.buffers.crypto:
            crypto.agent.receive_challenge(self.requester)

        # Re-add this event
        self.event_time += self.requester.challenge_response_period
        sim.add_event(self)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s})"

class AgentReceiveChallengeResponse(BaseCryptoEvent):
    def __init__(self, event_time: float, requester: Agent, agent: Agent, behaviour: InteractionObservation):
        super().__init__(event_time)
        self.requester = requester
        self.agent = agent
        self.behaviour = behaviour

    def action(self, sim: Simulator):
        super().action(sim)

        # Process response

        # We need to make sure we have their cryptographic information to process the response
        our_crypto = self._ensure_crypto_exists(sim, self.requester, self.agent)
        assert our_crypto

        self.requester.update_challenge_response(self.agent, self.behaviour)

    def __repr__(self):
        return f"{type(self).__name__}(req={self.requester!s})"
