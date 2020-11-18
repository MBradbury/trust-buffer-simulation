#!/bin/bash

BEHAVIOURS="AlwaysGoodBehaviour VeryGoodBehaviour GoodBehaviour"

ESs="Random FIFO LRU MRU"

rm -f *.pdf

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
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed 1 > "log-$ES.txt"

		./analysis.py metrics.pickle

		mv utility.pdf "$BEHAVIOUR/complete-buf-utility-$ES.pdf"
	done

	echo "-----------"

	# Some evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --num-agents 10 --num-capabilities 2 --duration 50 \
			--max-crypto-buf 10 --max-trust-buf 10 --max-reputation-buf 10 --max-stereotype-buf 10 \
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed 1 > "log-$ES.txt"

		./analysis.py metrics.pickle

		mv utility.pdf "$BEHAVIOUR/large-buf-utility-$ES.pdf"
	done

	echo "-----------"

	# Lots of evictions
	for ES in $ESs
	do
		echo "Running $ES"

		./run_simulation.py --num-agents 10 --num-capabilities 2 --duration 50 \
			--max-crypto-buf 5 --max-trust-buf 5 --max-reputation-buf 5 --max-stereotype-buf 5 \
			--eviction-strategy "$ES" --behaviour "$BEHAVIOUR" --seed 1 > log-$ES.txt

		./analysis.py metrics.pickle

		mv utility.pdf "$BEHAVIOUR/small-buf-utility-$ES.pdf"
	done

	echo "==========="
done
