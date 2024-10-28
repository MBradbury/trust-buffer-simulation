#!/usr/bin/env python
from __future__ import annotations

import argparse
from itertools import chain
import secrets

from simulation.agent import Agent
from simulation.agent_choose_behaviour import AgentChooseBehaviour
from simulation.capability import Capability
from simulation.capability_behaviour import CapabilityBehaviour
from simulation.eviction_strategy import EvictionStrategy
from simulation.simulator import Simulator
from simulation.utility_targets import UtilityTargets

def get_eviction_strategy(short_name: str) -> type[EvictionStrategy]:
    [cls] = [cls for cls in EvictionStrategy.__subclasses__() if cls.short_name == short_name]
    return cls

def get_behaviour(name: str) -> type[CapabilityBehaviour]:
    [cls] = [cls for cls in CapabilityBehaviour.__subclasses__() if cls.__name__ == name]
    return cls

def get_agent_choose_behaviour(name: str) -> type[AgentChooseBehaviour]:
    [cls] = [cls for cls in AgentChooseBehaviour.__subclasses__() if cls.short_name == name]
    return cls

def main(args):
    seed = args.seed if args.seed is not None else secrets.randbits(32)

    capabilities = [Capability(f"C{n}", args.task_period, n) for n in range(args.num_capabilities)]

    choose = get_agent_choose_behaviour(args.agent_choose)

    agent_behaviours = [
        [behaviour] * num_agents
        for (num_agents, behaviour) in args.agents
    ]

    # Assume that each agent has all capabilities
    agents = [
        Agent(f"A{n}",
              capabilities,
              get_behaviour(behaviour),
              choose,
              args.trust_dissem_period,
              args.challenge_response_period,
              args.challenge_execution_time,
              args.max_crypto_buf,
              args.max_trust_buf,
              args.max_reputation_buf,
              args.max_stereotype_buf,
              args.max_cr_buf,
              args.cuckoo_max_capacity,
              args.sequential_fails_threshold)

        for (n, behaviour) in enumerate(chain.from_iterable(agent_behaviours))
    ]

    # Validate that every agent has a unique EUI64
    euis = {agent.eui64 for agent in agents}
    if len(euis) != len(agents):
        raise RuntimeError("Generated a duplicate EUI64 for an agent")

    es = get_eviction_strategy(args.eviction_strategy)

    sim = Simulator(seed, agents, es, args.duration, args.utility_targets, args.log_level)

    sim.run(args.max_start_delay)

    sim.metrics.save(sim, args, args.path_prefix)

def eviction_strategies() -> list[str]:
    return [cls.short_name for cls in EvictionStrategy.__subclasses__()]

def behaviours() -> list[str]:
    return [cls.__name__ for cls in CapabilityBehaviour.__subclasses__()]

def agent_choose_behaviours() -> list[str]:
    return [cls.short_name for cls in AgentChooseBehaviour.__subclasses__()]

# From: https://stackoverflow.com/questions/8526675/python-argparse-optional-append-argument-with-choices
class AgentBehavioursAction(argparse.Action):
    CHOICES = behaviours()
    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            number = int(values[0])
            if number <= 0:
                message = f"invalid number: {number!r} (must be greater than 0)"
                raise argparse.ArgumentError(self, message)

            behaviour = values[1]
            if behaviour not in self.CHOICES:
                message = f"invalid choice: {behaviour!r} (choose from {', '.join(self.CHOICES)})"
                raise argparse.ArgumentError(self, message)

            if len(values) > 2:
                raise argparse.ArgumentError(self, f"too many arguments {values}")

            attr = getattr(namespace, self.dest)
            if attr is None:
                setattr(namespace, self.dest, [(number, behaviour)])
            else:
                setattr(namespace, self.dest, attr + [(number, behaviour)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simulate')
    parser.add_argument('--agents', required=True, nargs='+', metavar='num behaviour',
                        action=AgentBehavioursAction,
                        help='The number of agents to include in the simulation and the behaviour of those agents')

    parser.add_argument('--num-capabilities', type=int, required=False, default=2,
                        help='The number of capabilities that agents have')

    parser.add_argument('--duration', type=float, required=True,
                        help='The duration of the simulation')

    parser.add_argument('--max-start-delay', type=float, required=False, default=1.0,
                        help='The maximum random delay that an agent will wait for before starting')

    parser.add_argument('--trust-dissem-period', type=float, required=False, default=1.0,
                        help='The average time between trust dissemination')
    parser.add_argument('--task-period', type=float, required=False, default=1.0,
                        help='The average time between task interactions')

    parser.add_argument('--max-crypto-buf', type=int, required=True,
                        help='The maximum length of the crypto buffer')
    parser.add_argument('--max-trust-buf', type=int, required=True,
                        help='The maximum length of the trust buffer')
    parser.add_argument('--max-reputation-buf', type=int, required=True,
                        help='The maximum length of the reputation buffer')
    parser.add_argument('--max-stereotype-buf', type=int, required=True,
                        help='The maximum length of the stereotype buffer')
    parser.add_argument('--max-cr-buf', type=int, required=False, default=0,
                        help='The maximum length of the challenge-response buffer')
    parser.add_argument('--cuckoo-max-capacity', type=int, required=False, default=0,
                        help='Maximum capacity of cuckoo filter')

    parser.add_argument('--challenge-response-period', type=float, default=None,
                        help='If challenge-response is enabled, how often should challenge-response be sent')
    parser.add_argument('--challenge-execution-time', type=float, default=None,
                        help='How long it takes to execute a challenge')

    parser.add_argument('--sequential-fails-threshold', type=int, required=False, default=1,
                        help='Number of times a challenge needs to fail for an agent to be considered bad under Cuckoo')

    parser.add_argument('--eviction-strategy', type=str, required=True, choices=eviction_strategies(),
                        help='The eviction strategy')
    parser.add_argument('--agent-choose', type=str, required=True, choices=agent_choose_behaviours(),
                        help='The behaviour to choose which agent to interact with to perform a task')
    parser.add_argument('--utility-targets', type=UtilityTargets, required=True, choices=list(UtilityTargets),
                        help='Which targets to evaluate utility against')

    parser.add_argument('--path-prefix', type=str, required=False, default="./",
                        help='The path prefix for output files')

    parser.add_argument('--seed', type=int, required=False, default=None,
                        help='The simulation seed')

    parser.add_argument('--log-level', type=int, choices=(0, 1), required=False, default=1,
                        help='The log level')

    args = parser.parse_args()

    main(args)
