#!/usr/bin/env python
from __future__ import annotations

import os
import pickle
import itertools
from itertools import chain
import multiprocessing
import functools
import bz2

import numpy as np

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import seaborn

from utils.graphing import savefig
from simulation.metrics import Metrics
from simulation.capability_behaviour import CapabilityBehaviourState, InteractionObservation

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_utility(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(b.source, b.capability) for b in metrics.buffers}

    grouped_utility = {
        (asrc, acap): [
            (b.t, b.utility)

            for b in metrics.buffers
            if asrc == b.source and acap == b.capability
        ]
        for (asrc, acap) in sources_utilities
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}")

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Utility (\\%)')

    ax.legend(bbox_to_anchor=(1.275, 1), loc="upper right", ncol=1)

    savefig(fig, f"{path_prefix}utility.pdf")

    plt.close(fig)

def graph_max_utility(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(b.source, b.capability) for b in metrics.buffers}

    grouped_utility = {
        (asrc, acap): [
            (b.t, b.max_utility)

            for b in metrics.buffers
            if asrc == b.source and acap == b.capability
        ]
        for (asrc, acap) in sources_utilities
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}")

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Maximum Utility (\\%)')

    ax.legend(bbox_to_anchor=(1.275, 1), loc="upper right", ncol=1)

    savefig(fig, f"{path_prefix}max-utility.pdf")

    plt.close(fig)

def graph_utility_scaled(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(b.source, b.capability) for b in metrics.buffers}

    grouped_utility = {
        (asrc, acap): [
            (b.t, b.utility / b.max_utility)

            for b in metrics.buffers
            if asrc == b.source and acap == b.capability
        ]
        for (asrc, acap) in sources_utilities
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}")

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Normalised Utility (\\%)')
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

    ax.legend(bbox_to_anchor=(1.5, 1), loc="upper right", ncol=2)

    savefig(fig, f"{path_prefix}norm-utility.pdf")

    plt.close(fig)

def graph_utility_scaled_cap_colour(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(b.source, b.capability) for b in metrics.buffers}

    grouped_utility = {
        (asrc, acap): [
            (b.t, b.utility / b.max_utility)

            for b in metrics.buffers
            if asrc == b.source and acap == b.capability
        ]
        for (asrc, acap) in sources_utilities
    }

    sequential_cmaps = [seaborn.mpl_palette(name, n_colors=len(metrics.agent_names)) for name in ("Greens", "Purples")]
    cmap_for_cap = {
        c: sequential_cmaps[c]
        for c in {int(c[1:]) for c in metrics.capability_names}
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}", color=cmap_for_cap[int(cap[1:])][metrics.agent_names.index(src)])

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Normalised Utility (\\%)')
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, symbol=''))

    ax.legend(bbox_to_anchor=(1.5, 1), loc="upper right", ncol=2)

    savefig(fig, f"{path_prefix}norm-utility-cc.pdf")

    plt.close(fig)

def graph_utility_max_distance(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(b.source, b.capability) for b in metrics.buffers}

    grouped_utility = {
        (asrc, acap): [
            (b.t, b.max_utility - b.utility)

            for b in metrics.buffers
            if asrc == b.source and acap == b.capability
        ]
        for (asrc, acap) in sources_utilities
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}")

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Utility Distance (\\%)')

    ax.legend(bbox_to_anchor=(1.275, 1), loc="upper right", ncol=1)

    savefig(fig, f"{path_prefix}utility-distance.pdf")

    plt.close(fig)

def graph_behaviour_state(metrics: Metrics, path_prefix: str):
    agents, capabilities = zip(*metrics.behaviour_changes.keys())
    agents = list(sorted(set(agents)))
    capabilities = list(sorted(set(capabilities)))

    fig, axs = plt.subplots(nrows=len(agents), ncols=len(capabilities), sharex=True, squeeze=False, figsize=(18,20))

    yaxis_categories = [obs.name for obs in CapabilityBehaviourState]

    for (agent, cap) in itertools.product(agents, capabilities):
        try:
            behaviour = metrics.behaviour_changes[(agent, cap)]
        except KeyError:
            # Skip when there are no records
            continue

        # Skip when there were no interactions
        if not behaviour:
            continue

        X, Y = zip(*behaviour)
        Y = [y.name for y in Y]

        ax = axs[agents.index(agent), capabilities.index(cap)]

        ax.scatter(X, Y)

        ax.title.set_text(f"{agent} {cap}")

        #ax.set_xlim(min(X), max(X))
        #ax.plot([min(X)-100+i for i in range(len(yaxis_categories))], yaxis_categories)
        #ax.set_yticks(yaxis_categories)
        #ax.set_ylim(0 - 0.5, len(yaxis_categories) - 1 + 0.5)

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}behaviour_state.pdf")

    plt.close(fig)

def graph_interactions(metrics: Metrics, path_prefix: str):
    keys = {(b.target, b.capability) for b in metrics.buffers}

    all_interactions = {
        (target, capability): [
            (b.t, f"{b.outcome.name} (Imp)" if np.isnan(b.utility) else b.outcome.name)

            for b in metrics.buffers
            if b.target == target and b.capability == capability
        ]
        for (target, capability) in keys
    }

    agents, capabilities = zip(*all_interactions.keys())
    agents = list(sorted(set(agents)))
    capabilities = list(sorted(set(capabilities)))

    fig, axs = plt.subplots(nrows=len(agents), ncols=len(capabilities), sharex=True, squeeze=False, figsize=(18,20))

    yaxis_categories = [obs.name for obs in InteractionObservation]

    for (agent, cap) in itertools.product(agents, capabilities):
        try:
            interactions = all_interactions[(agent, cap)]
        except KeyError:
            # Skip when there are no records
            continue

        # Skip when there were no interactions
        if not interactions:
            continue

        X, Y = zip(*interactions)

        ax = axs[agents.index(agent), capabilities.index(cap)]

        ax.scatter(X, Y)

        ax.title.set_text(f"{agent} {cap}")

        #ax.set_xlim(min(X), max(X))
        #ax.plot([min(X)-100+i for i in range(len(yaxis_categories))], yaxis_categories)
        #ax.set_yticks(yaxis_categories)
        #ax.set_ylim(0 - 0.5, len(yaxis_categories) - 1 + 0.5)

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}interactions.pdf")

    plt.close(fig)

def graph_interactions_utility_hist(metrics: Metrics, path_prefix: str):

    correct = [
        b.utility
        for b
        in metrics.buffers
        if b.outcome == InteractionObservation.Correct
    ]

    incorrect = [
        b.utility
        for b
        in metrics.buffers
        if b.outcome == InteractionObservation.Incorrect
        if not np.isnan(b.utility)
    ]

    incorrect_imp = [
        b.utility
        for b
        in metrics.buffers
        if b.outcome == InteractionObservation.Incorrect
        if np.isnan(b.utility)
    ]

    bins = np.arange(0, 1, 0.02)

    fig = plt.figure()
    ax = fig.gca()

    ax.hist([
                correct,
                incorrect,
                incorrect_imp
            ],
            bins,
            histtype='bar',
            stacked=True,
            label=[
                f"Correct ({len(correct)})",
                f"Incorrect ({len(incorrect)})",
                f"Incorrect (Imp) ({len(incorrect_imp)})"
            ])
    ax.legend()

    ax.set_xlim(0, 1)

    ax.set_xlabel('Utility (\\%)')
    ax.set_ylabel('Interaction Count')

    savefig(fig, f"{path_prefix}interactions-utility-hist.pdf")

    plt.close(fig)

def graph_evictions(metrics: Metrics, path_prefix: str):
    columns = ["crypto", "trust", "reputation", "stereotype"]
    column_to_data = {
        "crypto": metrics.evicted_crypto,
        "trust": metrics.evicted_trust,
        "reputation": metrics.evicted_reputation,
        "stereotype": metrics.evicted_stereotype
    }

    agents = set(chain.from_iterable(
        {a for (t, a, i) in data}
        for data in column_to_data.values()
    ))
    agents = list(sorted(agents))

    def sanitise_i(column, i):
        if column == "crypto" or column == "reputation":
            return i[0]
        else:
            return f"{i[0]}-{i[1]}"


    all_evictions = {
        (agent, column): list(sorted([(t, sanitise_i(column, i)) for (t, a, i) in column_data if a == agent], key=lambda x: x[1]))
        for agent in agents
        for (column, column_data) in column_to_data.items()
    }

    fig, axs = plt.subplots(nrows=max(1, len(agents)), ncols=max(1, len(columns)), sharex=True, squeeze=False, figsize=(18,30))

    for (agent, col) in itertools.product(agents, columns):
        try:
            evictions = all_evictions[(agent, col)]
        except KeyError:
            # Skip when there are no evictions
            continue

        # Skip when there were no evictions
        if not evictions:
            continue

        X, Y = zip(*evictions)

        ax = axs[agents.index(agent), columns.index(col)]

        ax.scatter(X, Y)

        ax.title.set_text(f"{agent} {col}")

        ax.tick_params(axis='y', labelsize="small")

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}evictions.pdf")

    plt.close(fig)

def graph_interactions_performed(metrics: Metrics, path_prefix: str):

    all_interactions = {
        (agent, capability): [t for (t, a, c) in metrics.interaction_performed if a == agent and c == capability]
        for agent in metrics.agent_names
        for capability in metrics.capability_names
    }

    fig, axs = plt.subplots(nrows=len(metrics.agent_names), ncols=len(metrics.capability_names), sharex=True, squeeze=False, figsize=(18,30))

    for (agent, col) in itertools.product(metrics.agent_names, metrics.capability_names):
        try:
            interactions = all_interactions[(agent, col)]
        except KeyError:
            # Skip when there are no evictions
            continue

        # Skip when there were no evictions
        if not interactions:
            continue

        ax = axs[metrics.agent_names.index(agent), metrics.capability_names.index(col)]

        bins = np.arange(min(interactions), max(interactions), 5)

        ax.hist(interactions, bins, histtype='bar')

        ax.title.set_text(f"{agent} {col}")

        ax.tick_params(axis='y', labelsize="small")

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}interactions-performed.pdf")

    plt.close(fig)

def call(fn):
    fn()

def main(args):
    assert isinstance(args.metrics_path, str)
    with bz2.open(args.metrics_path, "rb") as f:
        metrics = pickle.load(f)

    fns = [graph_utility, graph_max_utility, graph_utility_scaled, graph_utility_scaled_cap_colour, graph_utility_max_distance,
           graph_behaviour_state, graph_interactions, graph_interactions_utility_hist,
           #graph_evictions,
           graph_interactions_performed]
    fns = [functools.partial(fn, metrics, args.path_prefix) for fn in fns]

    usable_cpus = len(os.sched_getaffinity(0))

    with multiprocessing.Pool(min(usable_cpus, len(fns))) as p:
        p.map(call, fns)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_path', type=str,
                        help='The path to the metrics to analyse')

    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    args = parser.parse_args()

    main(args)
