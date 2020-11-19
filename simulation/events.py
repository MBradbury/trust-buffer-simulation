from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering

from simulation.constants import EPSILON, BEHAVIOUR_UPDATE_PERIOD
from simulation.capability import InteractionObservation

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

    def action(self, sim: Simulation):
        super().action(sim)

        # Source needs target's crypto information to process response
        sim.es.use_crypto(self.source.buffers.find_crypto(self.target))

        # Want to use the same seed for the interaction that does occur and the potential interactions
        seed = sim.rng.getrandbits(32)

        # Did the target perform the interaction well?
        outcome = self.target.capability_behaviour[self.capability].next_interaction(seed, sim.current_time)

        # How would the other capabilities have performed?
        outcomes = {
            agent: agent.capability_behaviour[self.capability].peek_interaction(seed) if agent is not self.target else outcome
            for agent in sim.agents
            if agent is not self.source
        }
        self.log(sim, f"Outcomes|{outcomes}")
        sim.metrics.add_interaction_outcomes(sim.current_time, self.source, self.capability, outcomes)

        # Who are we interested in evaluating the utility of the buffers for?
        #utility_targets = [agent for (agent, outcome) in outcomes.items() if outcome is InteractionObservation.Correct]
        utility_targets = outcomes.keys()

        utility = self.buffers.utility(self.source, self.capability, targets=utility_targets)
        self.log(sim, f"Value of buffers {utility} {self.capability}")

        sim.metrics.add_buffer_evaluation(sim.current_time, self.source, self.capability, utility, self.target, outcome)

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
