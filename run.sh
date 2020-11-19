#!/bin/bash

BEHAVIOURS="AlwaysGoodBehaviour VeryGoodBehaviour GoodBehaviour"

ESs="Random FIFO LRU MRU Chen2016 FiveBand"

rm -f *.pdf

SEED=2

for BEHAVIOUR in $BEHAVIOURS
do
	echo "Running behaviour $BEHAVIOUR"

	rm -rf "$BEHAVIOUR"

	mkdir "$BEHAVIOUR"

	# No evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --num-agents 10 --num-capabilities 2 --duration 50 \
			--max-crypto-buf 10 --max-trust-buf 20 --max-reputation-buf 10 --max-stereotype-buf 20 \
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed $SEED > "log-$ES.txt"

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/complete-buf-$ES-"
	done

	echo "-----------"

	# Some evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --num-agents 10 --num-capabilities 2 --duration 50 \
			--max-crypto-buf 10 --max-trust-buf 10 --max-reputation-buf 10 --max-stereotype-buf 10 \
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed $SEED > "log-$ES.txt"

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/large-buf-$ES-"
	done

	echo "-----------"

	# Lots of evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --num-agents 10 --num-capabilities 2 --duration 50 \
			--max-crypto-buf 5 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed $SEED > log-$ES.txt

		./analysis.py metrics.pickle --path-prefix "$BEHAVIOUR/small-buf-$ES-"
	done

	echo "==========="
done
