#!/bin/bash

BEHAVIOUR="AlwaysGoodBehaviour"
NUM_BEHAVIOUR_AGENTS=2
NUM_BAD_AGENTS=8
NUM_CAPABILITIES=2
DURATION=300
ES="LRU"
AGENT_CHOOSE="Cuckoo"
UTILITY_TARGETS="good"

SEED=2

# python -OO -m cProfile -o out.prof run_simulation.py
python -OO run_simulation.py --agents $NUM_BEHAVIOUR_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
            --challenge-response-period 20 \
            --challenge-execution-time 5 \
			--max-crypto-buf 10 --max-trust-buf 20 --max-reputation-buf 10 --max-stereotype-buf 20 --max-cr-buf 10 --cuckoo-max-capacity 20 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "results/cuckoo/$BEHAVIOUR/$ES/complete-" --log-level 0
