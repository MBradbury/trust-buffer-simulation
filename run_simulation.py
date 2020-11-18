#!/usr/bin/env python3
from __future__ import annotations

from simulation.agent import *
from simulation.capability import *
from simulation.eviction_strategy import *
from simulation.events import *
from simulation.metrics import Metrics
from simulation.simulator import Simulator

def get_eviction_strategy(short_name: str):
    [cls] = [cls for cls in EvictionStrategy.__subclasses__() if cls.short_name == short_name]
    return cls

def get_behaviour(name: str):
    [cls] = [cls for cls in CapabilityBehaviour.__subclasses__() if cls.__name__ == name]
    return cls

def main(args):
    seed = args.seed if args.seed is not None else secrets.randbits(32)

    capabilities = [Capability(f"C{n}", args.task_period) for n in range(args.num_capabilities)]

    behaviour = get_behaviour(args.behaviour)

    # Assume that each agent has all capabilities
    agents = [
        Agent(f"A{n}", capabilities, behaviour, args.trust_dissem_period,
              args.max_crypto_buf, args.max_trust_buf,
              args.max_reputation_buf, args.max_stereotype_buf)
        for n in range(args.num_agents)
    ]

    es = get_eviction_strategy(args.eviction_strategy)

    sim = Simulator(seed, agents, es, args.duration)

    sim.run(args.max_start_delay)

    sim.metrics.save(sim)

def eviction_strategies():
    return [cls.short_name for cls in EvictionStrategy.__subclasses__()]

def behaviours():
    return [cls.__name__ for cls in CapabilityBehaviour.__subclasses__()]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Simulate')
    parser.add_argument('--num-agents', type=int, required=True,
                        help='The number of agents to include in the simulation')

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

    parser.add_argument('--behaviour', type=str, required=True, choices=behaviours(),
                        help='The behaviour of the agent capabilities')
    parser.add_argument('--eviction-strategy', type=str, required=True, choices=eviction_strategies(),
                        help='The eviction strategy')

    parser.add_argument('--seed', type=int, required=False, default=None,
                        help='The simulation seed')

    args = parser.parse_args()

    main(args)
