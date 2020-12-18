#!/bin/bash

function ctrl_c() {
	echo "** Trapped CTRL-C"
	exit 1
}

trap ctrl_c SIGINT

BEHAVIOURS=("VeryGoodBehaviour" "UnstableBehaviour" "GoodBehaviour" "AlwaysGoodBehaviour")

ESs=("CapPri" "None" "LRU" "LRU2" "Random" "FIFO" "MRU" "Chen2016" "FiveBand" "NotInOther" "MinNotInOther")

if [ -z "$SEED" ]
then
	SEED=2
fi

NUM_AGENTS=8
NUM_BAD_AGENTS=2
NUM_CAPABILITIES=2
DURATION=300
AGENT_CHOOSE=BRS
UTILITY_TARGETS=good

IFS=,
BE_PRODUCT=$(eval echo {"${BEHAVIOURS[*]}"}/{"${ESs[*]}"})

echo "SEED=$SEED"

for BEHAVIOUR in "${BEHAVIOURS[@]}"
do
	echo "Running behaviour $BEHAVIOUR"
	mkdir -p "$BEHAVIOUR"

	# No evictions
	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 10 --max-trust-buf 20 --max-reputation-buf 10 --max-stereotype-buf 20 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/complete-" --log-level 0
	done

	echo "-----------"

	# Some evictions
	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 10 --max-trust-buf 10 --max-reputation-buf 10 --max-stereotype-buf 10 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/large-" --log-level 0
	done

	echo "-----------"

	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 10 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/medium-" --log-level 0
	done

	echo "-----------"

	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 5 --max-trust-buf 10 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/medium2-" --log-level 0
	done

	echo "-----------"

	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 5 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 10 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/medium4-" --log-level 0
	done

	echo "-----------"

	# Lots of evictions
	for ES in "${ESs[@]}"
	do
		echo "Running $BEHAVIOUR/$ES $SEED"
		mkdir -p "$BEHAVIOUR/$ES"

		python3 -O run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 5 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED --path-prefix "$BEHAVIOUR/$ES/small-" --log-level 0
	done

	echo "==========="
done

echo "Done!"
