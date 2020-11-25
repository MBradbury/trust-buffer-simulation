from __future__ import annotations

class AgentChooseBehaviour:
    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[Agent]:
        raise NotImplementedError

class RandomAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "Random"

    def choose_agent_for_task(self, agent: Agent, capability: Capability) -> Optional[Agent]:
        return agent.sim.rng.choice([item for item in agent.buffers.crypto if capability in item.agent.capabilities])

class BRSAgentChooseBehaviour(AgentChooseBehaviour):
    short_name = "BRS"

    @staticmethod
    def trust_value(agent: Agent, a: Agent, capability: Capability):
        t = agent.buffers.find_trust(a, capability)
        s = agent.buffers.find_stereotype(a, capability)

        rt, rr, rs = 0, 0, 0
        rtc, rrc, rsc = 0, 0, 0

        if t is not None:
            rt = t.brs_trust()
            rtc = 1

        for r in agent.buffers.reputation:
            for rti in r.trust_items:
                if rti.agent is a and rti.capability is capability:
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
            option.agent: self.trust_value(agent, option.agent, capability) for option in options
        }
        max_trust_value = max(trust_values.values())

        return agent.sim.rng.choice([item for item in options if trust_values[item.agent] >= max_trust_value - 0.1])
