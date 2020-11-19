from __future__ import annotations

from simulation.agent import Agent
from simulation.capability import Capability, InteractionObservation

import pickle 
from pprint import pprint

class Metrics:
    def __init__(self):
        self.interaction_outcomes = []
        self.utility = []

        self.evicted_crypto = []
        self.evicted_trust = []
        self.evicted_reputation = []
        self.evicted_stereotype = []

    def add_interaction_outcomes(self, t: float, source: Agent, capability: Capability, outcomes: dict):
        pickleable_outcomes = {agent.name: outcome for (agent, outcome) in outcomes.items()}

        self.interaction_outcomes.append((t, source.name, capability.name, pickleable_outcomes))

    def add_buffer_evaluation(self, t: float, source: Agent, capability: Capability, utility: float, target: Agent, outcome: InteractionObservation):
        self.utility.append((t, source.name, capability.name, utility, target.name, outcome))

    def add_evicted_crypto(self, t: float, agent: Agent, choice):
        self.evicted_crypto.append((t, agent.name, choice.basic()))
    def add_evicted_trust(self, t: float, agent: Agent, choice):
        self.evicted_trust.append((t, agent.name, choice.basic()))
    def add_evicted_reputation(self, t: float, agent: Agent, choice):
        self.evicted_reputation.append((t, agent.name, choice.basic()))
    def add_evicted_stereotype(self, t: float, agent: Agent, choice):
        self.evicted_stereotype.append((t, agent.name, choice.basic()))

    def save(self, sim, args):
        # save information from sim

        self.args = args

        self.behaviour_changes = {
            (agent.name, capability.name): behaviour.state_history
            for agent in sim.agents
            for (capability, behaviour) in agent.capability_behaviour.items()
        }

        self.max_utilities = {
            agent.name: agent.buffers.max_utility()
            for agent in sim.agents
        }

        pprint(self.max_utilities)

        #pprint(self.interaction_outcomes)
        #pprint(self.utility)

        #pprint(self.behaviour_changes)

        print("crypto", len(self.evicted_crypto))
        print("trust", len(self.evicted_trust))
        print("reputation", len(self.evicted_reputation))
        print("stereotype", len(self.evicted_stereotype))

        with open("metrics.pickle", "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
