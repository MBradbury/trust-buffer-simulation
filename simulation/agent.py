from __future__ import annotations

import copy
import random
from typing import Any

from simulation.agent_choose_behaviour import AgentChooseBehaviour
from simulation.agent_buffers import AgentBuffers, ReputationItem, CryptoItem, TrustItem, StereotypeItem, ChallengeResponseItem
from simulation.capability import Capability
from simulation.capability_behaviour import CapabilityBehaviour
from simulation.events import AgentStereotypeRequest, AgentCryptoRequest, AgentTaskInteraction, InteractionObservation, AgentReceiveChallengeResponse
from simulation.constants import EPSILON

from scipy.stats import skewnorm

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.simulator import Simulator

class Agent:
    def __init__(self,
                 name: str,
                 capabilities: list[Capability],
                 behaviour: type[CapabilityBehaviour],
                 choose: type[AgentChooseBehaviour],
                 trust_dissem_period: float,
                 challenge_response_period: float | None,
                 challenge_execution_time: float | None,
                 crypto_bux_max: int,
                 trust_bux_max: int,
                 reputation_bux_max: int,
                 stereotype_bux_max: int,
                 cr_bux_max: int,
                 cuckoo: bool):
        self.name = name

        # Generate a EUI64, use the name as the random seed as this should be unique
        # We use a EUI64 as this is typically used by the target devices
        self.eui64 = random.Random(self.name).randbytes(8)

        self.capabilities = capabilities
        self.capability_behaviour = {capability: behaviour() for capability in self.capabilities}

        self.choose = choose()

        self.trust_dissem_period = trust_dissem_period

        # Is challenge-response enabled or not?
        self.challenge_response_period = challenge_response_period
        self.challenge_execution_time = challenge_execution_time
        self.challenge_response_behaviour = behaviour()

        if self.challenge_response_period is not None:
            if cr_bux_max <= 0:
                raise ValueError("Cannot enable challenge-response and have no buffer items")
            if self.challenge_execution_time is None:
                raise ValueError("Must set challenge_execution_time if challenge_response_period is set")

        self.buffers = AgentBuffers(self, crypto_bux_max, trust_bux_max, reputation_bux_max, stereotype_bux_max, cr_bux_max, cuckoo)

        self.sim: Simulator | None = None

    def set_sim(self, sim: Simulator):
        self.sim = sim

        # Give each behaviour their own random seed to prevent capabilities
        # all being good or bad simultaneously
        for (_capability, behaviour) in sorted(self.capability_behaviour.items(), key=lambda x: x[0].name):
            behaviour.individual_seed = sim.rng.getrandbits(32)

    def next_trust_dissemination_period(self, rng: random.Random) -> float:
        return rng.expovariate(1.0 / self.trust_dissem_period)

    def request_stereotype(self, agent: Agent):
        assert self.sim is not None
        self.sim.add_event(AgentStereotypeRequest(self.sim.current_time + EPSILON, self, agent))

    def request_crypto(self, agent: Agent):
        assert self.sim is not None
        self.sim.add_event(AgentCryptoRequest(self.sim.current_time + EPSILON, self, agent))

    def receive_trust_information(self, agent: Agent):
        assert self.sim is not None

        # Don't record information from ourself
        if agent is self:
            return

        crypto_item = self.buffers.find_crypto(agent)

        # Can't decrypt or verify
        if crypto_item is None:
            self.request_crypto(agent)
            return

        self.sim.es.use_crypto(crypto_item)

        # Need to request sterotype information here, if missing any
        if any(self.buffers.find_stereotype(agent, capability) is None for capability in self.capabilities):
            self.request_stereotype(agent)

        trust_items = copy.deepcopy(agent.buffers.trust)
        trust_items.freeze()

        # Record reputation information
        reputation_item = self.buffers.find_reputation(agent)
        if reputation_item is None:
            # Try to add this new item
            new_reputation_item = ReputationItem(agent, trust_items)

            self.buffers.add_reputation(self.sim.es, new_reputation_item)
        else:
            # Update the item
            reputation_item.trust_items = trust_items

            # Record that we have used it
            self.sim.es.use_reputation(reputation_item)


    def receive_crypto_information(self, agent: Agent):
        assert self.sim is not None

        # Don't record information about ourself
        if agent is self:
            return

        crypto_item = self.buffers.find_crypto(agent)

        # Don't add items we already have
        if crypto_item is not None:
            return

        new_crypto_item = CryptoItem(agent)

        self.buffers.add_crypto(self.sim.es, new_crypto_item)

    def receive_stereotype_information(self, agent: Agent, capability: Capability):
        assert self.sim is not None

        # Ignore stereotypes about ourself
        if agent is self:
            return

        # Don't want to record capabilities we do not have
        if capability not in self.capabilities:
            return

        stereotype_item = self.buffers.find_stereotype(agent, capability)

        # Don't add items we already have
        if stereotype_item is not None:
            return

        new_stereotype_item = StereotypeItem(agent, capability)

        self.buffers.add_stereotype(self.sim.es, new_stereotype_item)

    def update_trust_history(self, agent: Agent, capability: Capability, outcome: InteractionObservation):
        assert self.sim is not None

        trust_item = self.buffers.find_trust(agent, capability)

        # Need to add item if not in buffer
        if trust_item is None:
            new_trust_item = TrustItem(agent, capability)

            self.buffers.add_trust(self.sim.es, new_trust_item)

            trust_item = self.buffers.find_trust(agent, capability)
            assert trust_item is new_trust_item or trust_item is None

        if trust_item is not None:
            trust_item.record(outcome)

            # Record that we have used it
            self.sim.es.use_trust(trust_item)

        self.log(f"Value of buffers after update {self.buffers.utility(self, capability, targets=[agent])} {capability}")

    def choose_agent_for_task(self, capability: Capability):
        assert self.sim is not None

        item = self.choose.choose_agent_for_task(self, capability)
        if item is None:
            return None

        self.sim.es.use_crypto(item)

        self.sim.es.use_trust(self.buffers.find_trust(item.agent, capability))

        for reputation_item in self.buffers.reputation:
            if any(trust_item.agent is item and trust_item.capability is capability for trust_item in reputation_item.trust_items):
                self.sim.es.use_reputation(reputation_item)

        self.sim.es.use_stereotype(self.buffers.find_stereotype(item.agent, capability))

        return item.agent

    def perform_interaction(self, selected_agent: Agent, capability: Capability):
        assert self.sim is not None

        # Record the values in the buffers at the time the interaction was initiated
        buffers = self.buffers.frozen_copy()

        self.sim.add_event(AgentTaskInteraction(self.sim.current_time + EPSILON, self, capability, selected_agent, buffers))

    def receive_challenge(self, agent: Agent):
        assert self.sim is not None
        assert self.challenge_execution_time is not None

        behaviour = self.challenge_response_behaviour.next_interaction(self.sim.rng.getrandbits(32), self.sim.current_time)

        self.log(f"Received challenge from {agent} and behaving {behaviour}")

        if behaviour == InteractionObservation.Correct:
            # Behave well and send correct response on-time

            challenge_execution_time_random = skewnorm.rvs(loc=1, scale=1, a=10, random_state=self.sim.rng.getrandbits(32))
            challenge_execution_time = self.challenge_execution_time + challenge_execution_time_random

            self.sim.add_event(AgentReceiveChallengeResponse(self.sim.current_time + challenge_execution_time, self, agent, behaviour))
        else:
            # Choose how to behave incorrectly
            # Could do any of:
            # 1. Send incorrect result
            # 2. Send correct result late
            # 3. Do not reply
            # For simplicty will just model #1
            challenge_execution_time_random = skewnorm.rvs(loc=1, scale=1, a=10, random_state=self.sim.rng.getrandbits(32))
            challenge_execution_time = self.challenge_execution_time + challenge_execution_time_random

            self.sim.add_event(AgentReceiveChallengeResponse(self.sim.current_time + challenge_execution_time, self, agent, behaviour))

    def update_challenge_response(self, agent: Agent, outcome: InteractionObservation):
        assert self.sim is not None

        # Record seen
        if self.buffers.encountered is not None:
            self.buffers.encountered.insert(agent.eui64)

        cr_item = self.buffers.find_challenge_response(agent)

        # Need to add item if not in buffer
        if cr_item is None:
            new_cr_item = ChallengeResponseItem(agent, outcome == InteractionObservation.Correct)

            self.buffers.add_challenge_response(self.sim.es, new_cr_item)

            cr_item = self.buffers.find_challenge_response(agent)
            assert cr_item is new_cr_item or cr_item is None

        if cr_item is not None:
            cr_item.record(outcome)

            # Record in cuckoo filters the stats
            if self.buffers.badlist is not None:
                if cr_item.good:
                    self.buffers.badlist.delete(agent.eui64)
                else:
                    self.buffers.badlist.insert(agent.eui64)

            # Record that we have used it
            self.sim.es.use_challenge_response(cr_item)

        #self.log(f"Value of buffers after update {self.buffers.utility(self, targets=[agent])}")
        self.log(f"update_challenge_response {agent} {outcome} {cr_item}")

    def log(self, message: str):
        assert self.sim is not None
        self.sim.log(f"{self!s}|{message}")

    def __repr__(self):
        return f"Agent({self.name})"

    def __str__(self):
        return self.name

    # Can't allow this to be copied
    def __deepcopy__(self, memo: Any):
        return self

    # Can't allow this to be copied
    def __copy__(self):
        return self
