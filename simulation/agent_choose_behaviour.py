from __future__ import annotations

from typing import Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.agent import Agent
    from simulation.agent_buffers import AgentBuffers, CryptoItem
    from simulation.capability import Capability

class AgentChooseBehaviour:
    short_name = "Base"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[CryptoItem]:
        raise NotImplementedError

class RandomAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "Random"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[CryptoItem]:
        assert agent.sim is not None
        try:
            return agent.sim.rng.choice([item for item in agent.buffers.crypto if capability in item.agent.capabilities])
        except IndexError:
            return None

class BRSAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "BRS"

    @staticmethod
    def trust_value(buffers: AgentBuffers, agent: Agent, capability: Capability):
        t = buffers.find_trust(agent, capability)
        s = buffers.find_stereotype(agent, capability)

        rt, rr, rs = 0, 0, 0
        rtc, rrc, rsc = 0, 0, 0

        if t is not None:
            rt = t.brs_trust()
            rtc = 1

        for r in buffers.reputation:
            for rti in r.trust_items:
                if rti.agent is agent and rti.capability is capability:
                    rr += rti.brs_trust()
                    rrc += 1

        if rrc > 0:
            rr = rr / rrc
            rrc = 1

        if s is not None:
            stereo = s.agent.capability_behaviour[s.capability].brs_stereotype
            rs = stereo[0] / (stereo[0] + stereo[1])
            rsc = 1

        try:
            return (rt + rr + rs) / (rtc + rrc + rsc)
        except ZeroDivisionError:
            return 0

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[CryptoItem]:
        assert agent.sim is not None

        # Needs to be in crypto
        options = [item for item in agent.buffers.crypto if capability in item.agent.capabilities]
        if not options:
            return None

        trust_values = {
            option.agent: self.trust_value(agent.buffers, option.agent, capability) for option in options
        }
        max_trust_value = max(trust_values.values())

        try:
            return agent.sim.rng.choice([item for item in options if trust_values[item.agent] >= max_trust_value - 0.1])
        except IndexError:
            return None

class ChallengeResponseAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "CR"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[CryptoItem]:
        assert agent.sim is not None

        # Needs to be in crypto
        options = [item for item in agent.buffers.crypto if capability in item.agent.capabilities]
        if not options:
            return None

        # Needs to be good in challenge-response buffer
        options = [
            item
            for item in options
            for cr in [agent.buffers.find_challenge_response(item.agent)]
            if cr is not None and cr.good
        ]

        try:
            return agent.sim.rng.choice(options)
        except IndexError:
            return None

class CuckooAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "Cuckoo"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[CryptoItem]:
        assert agent.sim is not None
        assert agent.buffers.badlist is not None
        assert agent.buffers.encountered is not None

        # Needs to be in crypto
        options = [item for item in agent.buffers.crypto if capability in item.agent.capabilities]
        if not options:
            return None

        # Levels of preference
        # 1. Is not in badlist and is in encountered (seen and known to be good)
        # 2. Is not in encountered (not previously seen)
        # 3. Is in badlist (known to be bad)

        # Try and find items that are not in the badlist that we have encountered
        options = [
            item
            for item in options
            if not agent.buffers.badlist.contains(item.agent.eui64)
            if agent.buffers.encountered.contains(item.agent.eui64)
        ]

        # No seen and known to be good items
        if not options:
            # Fall back to not previously seen items
            options = [
                item
                for item in options
                if not agent.buffers.badlist.contains(item.agent.eui64)
                if not agent.buffers.encountered.contains(item.agent.eui64)
            ]

        if not options:
            # No good options at this point, everyone is known to be bad
            assert all(agent.buffers.badlist.contains(item.agent.eui64) for item in options)

        try:
            return agent.sim.rng.choice(options)
        except IndexError:
            return None
