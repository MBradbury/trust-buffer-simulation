# Description

This repository contains a discrete event simulator to evaluate trust-based interactions between agents with limited memory.

Memory is represented via four buffers with fixed sizes:
 1. Cryptographic
 2. Trust
 3. Reputation
 4. Stereotypes

Different buffer eviction strategies are implemented to evaluate which produces the highest utility of information contained in those buffers.

# Requirements

```bash
sudo apt-get install python3 cm-super graphviz
python3 -m pip install matplotlib numpy scipy hmmlearn tqdm pygraphviz seaborn
```

# Running an Experiment

`run.sh` defines running multiple eviction strategies and agent behaviours for different sized buffers.
`run_multiple.py` can be used to obtain a large number of repeats and `run-graphics.sh` can be used to obtain graph results for an individual run.

```bash
python3 run_multiple.py
```

To perform a run with a specific seed call `run.sh` or `run-graphics.sh` such as:
```bash
SEED=10 ./run.sh
```

# Analysing Results

## Graphing Individual Results

`./analyse_individual.py` create graphs for a single simulation.

```bash
./graph_individual.py <Behaviour>/<Eviction Strategy>/<buffer size>-metrics.<seed>.pickle.bz2
```

## Combining Results

Individual results need to be combined for them to be graphed

```bash
./combine_results.py VeryGoodBehaviour/* AlwaysGoodBehaviour/* UnstableBehaviour/* GoodBehaviour/*
```

## Graphing Combined Results

```bash
./graph_multiple.py VeryGoodBehaviour/* AlwaysGoodBehaviour/* UnstableBehaviour/* GoodBehaviour/*
```

## Creating a graph showing space usage

Trust models with different sizes will consume different amounts of space. The following script can be used to visualise this.

```bash
./graph_space.py VeryGoodBehaviour/* AlwaysGoodBehaviour/* UnstableBehaviour/* GoodBehaviour/*
```

## Creating graphs of buffer evolution over time

The following script can be used to visualise the evolution of buffer content over time.

```bash
mkdir -p "<out-dir>/"
./graph_buffers.py <Behaviour>/<Eviction Strategy>/<buffer size>-metrics.<seed>.pickle.bz2 --path-prefix "<out-dir>/"
```
