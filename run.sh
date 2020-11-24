#!/bin/bash

BEHAVIOURS="UnstableBehaviour AlwaysGoodBehaviour VeryGoodBehaviour GoodBehaviour"

ESs="Random FIFO LRU MRU Chen2016 FiveBand"

rm -f *.pdf

SEED=2
NUM_AGENTS=8
NUM_BAD_AGENTS=2
NUM_CAPABILITIES=2
DURATION=120
AGENT_CHOOSE=Random
UTILITY_TARGETS=good

for BEHAVIOUR in $BEHAVIOURS
do
	echo "Running behaviour $BEHAVIOUR"

	rm -rf "$BEHAVIOUR"

	mkdir "$BEHAVIOUR"

	# No evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 10 --max-trust-buf 20 --max-reputation-buf 10 --max-stereotype-buf 20 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED > "log-$ES.txt"

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/complete-buf-$ES-"
	done

	echo "-----------"

	# Some evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 10 --max-trust-buf 10 --max-reputation-buf 10 --max-stereotype-buf 10 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED > "log-$ES.txt"

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/large-buf-$ES-"
	done

	echo "-----------"

	# Lots of evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --agents $NUM_AGENTS $BEHAVIOUR --agents $NUM_BAD_AGENTS AlwaysBadBehaviour \
			--num-capabilities $NUM_CAPABILITIES --duration $DURATION \
			--max-crypto-buf 5 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --agent-choose "$AGENT_CHOOSE" --utility-targets "$UTILITY_TARGETS" \
			--seed $SEED > log-$ES.txt

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/small-buf-$ES-"
	done

	echo "==========="
done
