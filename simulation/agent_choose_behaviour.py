from __future__ import annotations

class AgentChooseBehaviour:
    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[Agent]:
        raise NotImplementedError

class RandomAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "Random"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[Agent]:
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

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[Agent]:
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
