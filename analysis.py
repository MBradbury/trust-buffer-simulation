#!/usr/bin/env python3
from __future__ import annotations

import pickle
import subprocess
import itertools

import matplotlib as mpl
import matplotlib.pyplot as plt

from simulation.metrics import Metrics
from simulation.capability import CapabilityBehaviourState, InteractionObservation

plt.rcParams['text.usetex'] = True
plt.rcParams['font.size'] = 12

def graph_utility(metrics: Metrics, path_prefix: str):
    fig = plt.figure()
    ax = fig.gca()

    sources_utilities = {(src, cap) for (t, src, cap, util, target, outcome) in metrics.utility}

    grouped_utility = {
        (asrc, acap): [
            (t, util)

            for (t, src, cap, util, target, outcome) in metrics.utility
            if asrc == src and acap == cap
        ]
        for (asrc, acap) in sources_utilities
    }

    for ((src, cap), utilities) in sorted(grouped_utility.items(), key=lambda x: x[0]):
        X, Y = zip(*utilities)
        ax.plot(X, Y, label=f"{src} {cap}")

    ax.set_ylim(0, 1)

    ax.set_xlabel('Time (secs)')
    ax.set_ylabel('Utility (\\%)')

    ax.legend()

    savefig(fig, f"{path_prefix}utility.pdf")

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

        ax.set_ylim(0 - 0.5, len(yaxis_categories) - 1 + 0.5)
        ax.set_yticks(yaxis_categories)

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}behaviour_state.pdf")

def graph_interactions(metrics: Metrics, path_prefix: str):
    keys = {(target, capability) for (t, source, capability, utility, target, outcome) in metrics.utility}

    all_interactions = {
        (target, capability): [
            (ut, uoutcome)

            for (ut, usource, ucapability, uutility, utarget, uoutcome) in metrics.utility
            if utarget == target and ucapability == capability
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
        Y = [y.name for y in Y]

        ax = axs[agents.index(agent), capabilities.index(cap)]

        ax.scatter(X, Y)

        ax.title.set_text(f"{agent} {cap}")

        ax.set_ylim(0 - 0.5, len(yaxis_categories) - 1 + 0.5)
        ax.set_yticks(yaxis_categories)

    fig.subplots_adjust(hspace=0.35)

    savefig(fig, f"{path_prefix}interactions.pdf")


def check_fonts(path: str):
    r = subprocess.run(f"pdffonts {path}",
        shell=True,
        check=True,
        capture_output=True,
        universal_newlines=True,
        encoding="utf-8",
    )

    if "Type 3" in r.stdout:
        raise RuntimeError(f"Type 3 font in {path}")

def savefig(fig, target: str, crop=False):
    fig.savefig(target, bbox_inches='tight')

    if crop:
        subprocess.run(f"pdfcrop {target} {target}", shell=True)

    print("Produced:", target)
    check_fonts(target)

def main(args):
    with open(args.metrics_path, "rb") as f:
        metrics = pickle.load(f)

    graph_utility(metrics, args.prefix)
    graph_behaviour_state(metrics, args.prefix)
    graph_interactions(metrics, args.prefix)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Analyse')
    parser.add_argument('metrics_path', type=str,
                        help='The path to the metrics to analyse')

    parser.add_argument('--path-prefix', type=str, default="",
                        help='The prefix to the location to output results')

    args = parser.parse_args()

    main(args)
